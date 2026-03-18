"""
Integration Test Suite - Links Flask API with Performance Evaluation

This script tests the plagiarism detection system by:
1. Creating/using sample test documents
2. Calling the Flask API endpoints
3. Collecting predictions
4. Calculating performance metrics (Accuracy, Precision, Recall, F1)
5. Validating the system works as expected
"""

import os
import sys
import requests
import json
from io import BytesIO
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# Flask API Configuration
API_URL = "http://localhost:5000/compare"
TIMEOUT = 10  # seconds

# Test Data: Ground truth labels
# 1 = Plagiarized, 0 = Original
TEST_CASES = [
    {
        "name": "Test 1: Original Academic Paper A",
        "text1": """Machine learning is a subset of artificial intelligence that enables systems 
        to learn and improve from experience without explicit programming. The field has grown 
        exponentially in recent years, with applications spanning computer vision, natural language 
        processing, and autonomous systems. Early research in pattern recognition laid the foundation 
        for modern machine learning algorithms. Today, deep learning architectures like neural networks 
        have revolutionized how we approach complex computational problems.""",
        "text2": """Deep learning represents a significant advancement in the field of artificial intelligence. 
        Unlike traditional programming approaches, deep learning systems discover the representations 
        needed for detection and classification from raw input. This paradigm shift has enabled breakthrough 
        performance in image recognition, speech processing, and game-playing systems. The success of deep 
        learning is largely attributable to the availability of large datasets and computational power.""",
        "label": 0  # Original - Different content, similar topic
    },
    {
        "name": "Test 2: Original Academic Paper B",
        "text1": """Climate change represents one of the most pressing environmental challenges of our time. 
        Rising global temperatures are causing shifts in precipitation patterns, melting of polar ice caps, 
        and increased frequency of extreme weather events. Scientists worldwide have documented compelling 
        evidence linking these changes to greenhouse gas emissions from human activities.""",
        "text2": """Renewable energy sources such as solar and wind power offer promising solutions to reduce 
        carbon emissions. These technologies have become increasingly cost-effective in recent years, making 
        them viable alternatives to fossil fuels. Government incentives and technological improvements continue 
        to drive adoption of renewable energy infrastructure globally.""",
        "label": 0  # Original - Completely different topics
    },
    {
        "name": "Test 3: Original Academic Paper C",
        "text1": """Quantum computing leverages quantum mechanical phenomena to perform computations that would be impossible on classical computers. Quantum bits, or qubits, can exist in superposition, allowing parallel 
        processing of multiple states simultaneously. This fundamental difference enables exponential speedup for 
        certain classes of problems, particularly in cryptography and optimization.""",
        "text2": """The evolution of computing has progressed through several distinct eras: mechanical calculation, 
        electronic computation, microprocessor-based systems, and now distributed cloud computing. Each generation 
        brought exponential increases in processing power and speed. Modern computers can perform billions of operations 
        per second, enabling analysis of massive datasets and complex simulations.""",
        "label": 0  # Original - Different computing concepts
    },
    {
        "name": "Test 4: Original Academic Paper D",
        "text1": """Blockchain technology provides a decentralized and tamper-proof mechanism for recording transactions. 
        Each block contains cryptographic hashes of previous blocks, creating an immutable chain of records. This 
        innovation has enabled cryptocurrency systems but also has applications beyond finance in supply chain management 
        and smart contracts.""",
        "text2": """Cybersecurity threats continue to evolve as attackers develop sophisticated techniques to breach systems. 
        Common attack vectors include phishing, malware injection, and exploitation of software vulnerabilities. Organizations 
        must implement multi-layered security strategies including encryption, access controls, and security awareness training.""",
        "label": 0  # Original - Different security topics
    },
    {
        "name": "Test 5: Original Academic Paper E",
        "text1": """Network architecture design is critical for ensuring reliable and efficient communication between systems. 
        Internet protocols establish standardized rules for data transmission, enabling interoperability across diverse 
        hardware platforms. Modern networks employ layered architectures (OSI model) to separate concerns and improve 
        system maintainability and scalability.""",
        "text2": """Software development methodologies have evolved from waterfall approaches to agile frameworks. Agile practices 
        emphasize iterative development, continuous testing, and adaptive planning. These approaches have proven effective in 
        managing complexity in modern software projects, particularly in environments with rapidly changing requirements.""",
        "label": 0  # Original - Different CS topics
    },
    {
        "name": "Test 6: Plagiarized - Direct Copy",
        "text1": """Machine learning is a subset of artificial intelligence that enables systems to learn and improve from 
        experience without explicit programming. The field has revolutionized computer science and brought significant advances 
        in natural language processing and computer vision.""",
        "text2": """Machine learning is a subset of artificial intelligence that enables systems to learn and improve from 
        experience without explicit programming. The field has revolutionized computer science and brought significant advances 
        in natural language processing and computer vision.""",
        "label": 1  # Plagiarized - Identical text
    },
    {
        "name": "Test 7: Plagiarized - Minor Changes",
        "text1": """Deep learning represents a significant advancement in the field of artificial intelligence. Unlike traditional 
        programming approaches, deep learning systems discover the representations needed for detection and classification tasks. 
        This paradigm shift has enabled breakthrough performance in image recognition and speech processing.""",
        "text2": """Deep learning represents an important advancement in artificial intelligence. Unlike standard programming 
        approaches, deep learning systems discover the representations needed for detection and classification. This paradigm 
        shift has enabled breakthrough performance in image recognition and speech processing.""",
        "label": 1  # Plagiarized - Paraphrased text (may have lower score)
    },
    {
        "name": "Test 8: Plagiarized - Reordered Sentences",
        "text1": """Climate change represents one of the most pressing environmental challenges. Rising global temperatures cause shifts 
        in precipitation patterns and melting of polar ice. Scientists have documented evidence linking these changes to greenhouse 
        gas emissions from human activities.""",
        "text2": """Scientists have documented evidence linking environmental changes to greenhouse gas emissions from human activities. 
        Climate change represents one of the most pressing environmental challenges. Rising global temperatures cause shifts in 
        precipitation patterns and melting of polar ice.""",
        "label": 1  # Plagiarized - Same content, reordered
    },
    {
        "name": "Test 9: Plagiarized - Partial Copy",
        "text1": """Blockchain technology provides a decentralized and tamper-proof mechanism for recording transactions. Each block contains 
        cryptographic hashes of previous blocks, creating an immutable chain of records. This innovation has enabled cryptocurrency 
        systems and has applications in supply chain management.""",
        "text2": """Blockchain technology provides a decentralized and tamper-proof mechanism for recording transactions. Each block contains 
        cryptographic hashes of previous blocks, creating an immutable chain of records. Distributed ledger systems ensure consensus across 
        network participants using specialized algorithms.""",
        "label": 1  # Plagiarized - First part is copied
    },
    {
        "name": "Test 10: Plagiarized - With Additional Content",
        "text1": """Network architecture design is critical for ensuring reliable communication between systems. Internet protocols establish 
        standardized rules for data transmission, enabling interoperability across diverse platforms. Modern networks employ layered architectures 
        to separate concerns and improve maintainability.""",
        "text2": """Network architecture design is critical for ensuring reliable communication between systems. Internet protocols establish 
        standardized rules for data transmission, enabling interoperability across diverse platforms. Modern networks employ layered architectures 
        to separate concerns and improve maintainability. These layers include the physical, data link, network, transport, session, presentation, 
        and application layers, each serving distinct functions.""",
        "label": 1  # Plagiarized - Original content + additional text
    }
]


def create_test_file(text, filename):
    """Create a temporary text file from content"""
    filepath = f"temp_{filename}.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    return filepath


def cleanup_test_files(files):
    """Remove temporary test files"""
    for filepath in files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not delete {filepath}: {e}")


def test_plagiarism_detection():
    """Run integration tests on plagiarism detection API"""
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Plagiarism Detection System")
    print("Testing Flask API with Real Predictions")
    print("=" * 80)
    
    predictions = []
    true_labels = []
    test_results = []
    
    # Run all test cases
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[Test {i}/10] {test_case['name']}")
        
        # Create temporary files
        file1_path = create_test_file(test_case['text1'], f"doc1_{i}")
        file2_path = create_test_file(test_case['text2'], f"doc2_{i}")
        
        try:
            # Call API
            with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
                files = {
                    'file1': f1,
                    'file2': f2
                }
                response = requests.post(API_URL, files=files, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                similarity = data['similarity']
                prediction = data['prediction']
                status = data['status']
                true_label = test_case['label']
                
                predictions.append(prediction)
                true_labels.append(true_label)
                
                # Store results
                test_results.append({
                    'test_num': i,
                    'name': test_case['name'],
                    'similarity': similarity,
                    'prediction': prediction,
                    'true_label': true_label,
                    'status': status,
                    'correct': prediction == true_label
                })
                
                # Display result
                match_symbol = "✓" if prediction == true_label else "✗"
                print(f"  Similarity: {similarity}%")
                print(f"  Prediction: {status} (pred={prediction}, true={true_label}) {match_symbol}")
            else:
                print(f"  ✗ API Error: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Connection Error: Flask server not running at {API_URL}")
            print(f"  Please start the Flask server: python app.py")
            return None
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
        finally:
            # Cleanup
            cleanup_test_files([file1_path, file2_path])
    
    return predictions, true_labels, test_results


def calculate_metrics(y_true, y_pred):
    """Calculate performance metrics"""
    
    try:
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred)
        rec = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        
        return {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1
        }
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None


def print_report(metrics, test_results=None):
    """Print formatted performance report"""
    
    if metrics is None:
        return
    
    print("\n" + "=" * 80)
    print("--- SEN501 Group 5: PERFORMANCE REPORT ---")
    print("Plagiarism Detection System - Live API Testing")
    print("=" * 80)
    
    acc = metrics['accuracy']
    prec = metrics['precision']
    rec = metrics['recall']
    f1 = metrics['f1']
    
    print(f"\n📊 CORE METRICS:")
    print(f"   Accuracy:  {acc:.1%}  - Overall correctness of predictions")
    print(f"   Precision: {prec:.2f}   - Accuracy of plagiarism predictions")
    print(f"   Recall:    {rec:.2f}   - Detection rate of actual plagiarism")
    print(f"   F1-Score:  {f1:.2f}   - Balanced precision-recall metric")
    
    print(f"\n🎯 INTERPRETATION:")
    if f1 >= 0.9:
        print(f"   ✅ EXCELLENT: System is highly reliable and ready for production")
    elif f1 >= 0.7:
        print(f"   ⚠️  GOOD: System works well but may need threshold tuning")
    else:
        print(f"   ❌ NEEDS WORK: Consider adjusting threshold or algorithm parameters")
    
    print(f"\n📋 DETAILED TEST RESULTS:")
    if test_results:
        print(f"\n{'Test':<6} {'Name':<40} {'Similarity':<12} {'Correct':<8}")
        print("-" * 80)
        for result in test_results:
            correct_symbol = "✓" if result['correct'] else "✗"
            test_name = result['name'][:38]
            print(f"{result['test_num']:<6} {test_name:<40} {result['similarity']:>6}% {correct_symbol:>7}")
    
    print("\n" + "=" * 80)
    
    # Classification report
    y_true = [r['true_label'] for r in test_results] if test_results else None
    y_pred = [r['prediction'] for r in test_results] if test_results else None
    
    if y_true and y_pred:
        print("\n📈 CLASSIFICATION REPORT:")
        print(classification_report(y_true, y_pred, target_names=["Original", "Plagiarized"]))
    
    print("=" * 80)


def main():
    """Main test execution"""
    
    print("\n⏳ Starting plagiarism detection integration tests...")
    print(f"   API Endpoint: {API_URL}")
    print(f"   Total Tests: {len(TEST_CASES)}")
    
    # Run tests
    result = test_plagiarism_detection()
    
    if result is None:
        print("\n❌ Tests could not complete. See error messages above.")
        sys.exit(1)
    
    predictions, true_labels, test_results = result
    
    # Calculate metrics
    metrics = calculate_metrics(true_labels, predictions)
    
    # Print report
    print_report(metrics, test_results)
    
    # Return success/failure
    if metrics['f1'] >= 0.8:
        print("\n✅ SYSTEM VALIDATION: PASSED")
        return 0
    else:
        print("\n⚠️  SYSTEM VALIDATION: NEEDS ATTENTION")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
