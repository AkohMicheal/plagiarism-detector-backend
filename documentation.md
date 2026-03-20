# Technical Documentation - Plagiarism Detection System

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Algorithm & Methodology](#algorithm--methodology)
3. [API Reference](#api-reference)
4. [Text Preprocessing](#text-preprocessing)
5. [Similarity Metrics](#similarity-metrics)
6. [Performance Analysis](#performance-analysis)
7. [Testing & Validation](#testing--validation)
8. [Configuration Guide](#configuration-guide)

---

## Architecture Overview

### System Components

```
User/Client
    ↓
Flask API (/compare endpoint)
    ↓
Text Extraction Layer (PDF/DOCX/TXT)
    ↓
TF-IDF Vectorization (2,3-grams)
    ↓
Cosine Similarity Calculation
    ↓
Classification (Threshold: 20.0)
    ↓
JSON Response (similarity %, prediction, status)
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Flask 2.x | HTTP server & routing |
| Text Analysis | scikit-learn | TF-IDF vectorization & cosine similarity |
| Document Parsing | PyPDF2, python-docx | Extract text from multiple formats |
| Cross-origin | Flask-CORS | Enable frontend integration |
| Validation | Custom metrics | Accuracy, Precision, Recall, F1 |

---

## Algorithm & Methodology

### Step 1: Text Extraction

Files are converted to plaintext using format-specific parsers:

```python
def extract_text(file):
    if file.endswith('.pdf'):
        # PyPDF2 extracts text page-by-page
    elif file.endswith('.docx'):
        # python-docx extracts paragraphs
    else:
        # Direct UTF-8 decode for .txt
```

**Supported Formats**: PDF, DOCX, TXT

### Step 2: TF-IDF Vectorization with N-grams

**Why N-grams (2,3)?**

- **Bigrams (2)**: Captures 2-word phrases (e.g., "academic integrity")
- **Trigrams (3)**: Captures 3-word phrases (e.g., "the quick brown")
- **Why not unigrams**: Avoids false positives from common single words ("the", "and", "is")

**Implementation:**

```python
vectorizer = TfidfVectorizer(ngram_range=(2, 3))
tfidf_matrix = vectorizer.fit_transform([text1, text2])
```

**Result**: Each document becomes a sparse vector of TF-IDF weights representing occurrence and importance of n-grams.

#### TF-IDF Formula

$$
\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)
$$

Where:
- **TF (Term Frequency)**: How often n-gram $t$ appears in document $d$
- **IDF (Inverse Document Frequency)**: $\log\left(\frac{N}{df_t}\right)$ where $N$ is total documents and $df_t$ is count of documents containing $t$

### Step 3: Cosine Similarity

Measures angle between two document vectors:

$$
\text{Cosine Similarity} = \frac{\vec{d_1} \cdot \vec{d_2}}{|\vec{d_1}| \times |\vec{d_2}|}
$$

**Range**: 0 (completely different) to 1 (identical)  
**Converted to percentage**: Multiplied by 100 for readability

```python
score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
```

### Step 4: Classification

Binary classification using threshold comparison:

```python
THRESHOLD = 20.0  # Calibrated for academic plagiarism detection
prediction = 1 if score >= THRESHOLD else 0
status = "Plagiarized" if prediction == 1 else "Original"
```

---

## API Reference

### Endpoint: POST `/compare`

**Purpose**: Compare two documents for plagiarism

**Request Format**:
```bash
curl -X POST \
  -F "file1=@document1.pdf" \
  -F "file2=@document2.pdf" \
  http://localhost:5000/compare
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file1 | File | Yes | First document (PDF/DOCX/TXT) |
| file2 | File | Yes | Second document (PDF/DOCX/TXT) |

**Success Response** (200 OK):
```json
{
  "similarity": 45.32,
  "prediction": 1,
  "status": "Plagiarized"
}
```

**Fields**:
| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| similarity | float | 0-100 | Cosine similarity % |
| prediction | int | 0 or 1 | 1=Plagiarized, 0=Original |
| status | string | - | Human-readable label |

**Error Response** (400 Bad Request):
```json
{
  "error": "Please upload two files"
}
```

---

## Text Preprocessing

### Current Implementation (Basic)

The system currently uses text as-is. For production, consider:

### Recommended Enhancements

```python
import re

def normalize_text(text):
    # Lowercase
    text = text.lower()
    
    # Remove punctuation (optional - keep for phrase matching)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Collapse whitespace
    text = ' '.join(text.split())
    
    # Optional: Remove stopwords for semantic analysis
    
    return text
```

**Tradeoff**: Aggressive normalization improves recall but reduces precision.

---

## Similarity Metrics

### Interpreting Similarity Scores

| Score Range | Interpretation | Action |
|-------------|-----------------|--------|
| 0-10 | Completely different | ✅ Original |
| 10-20 | Minimal overlap | ✅ Original |
| 20-40 | Moderate overlap | ⚠️ Review recommended |
| 40-70 | Significant overlap | 🚨 Likely plagiarized |
| 70-100 | Nearly identical | 🚨 Definitely plagiarized |

**Threshold = 20.0**: Separates topical similarity from actual plagiarism.

### Why Cosine Similarity?

✅ **Advantages**:
- Magnitude-independent (long vs short documents)
- Fast computation
- Geometric intuition (angle between vectors)

❌ **Limitations**:
- Ignores word order (bag-of-words)
- Cannot detect paraphrased plagiarism
- Susceptible to false positives from common phrasing

---

## Performance Analysis

### Evaluation Methodology

**Test Dataset**: 10 document pairs
- 5 original pairs (different authors, different topics)
- 5 plagiarized pairs (identical or near-identical)

**Ground Truth Labels**:
```python
y_true = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
```

### Metrics Definition

#### Accuracy
$$
\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{FP} + \text{TN} + \text{FN}}
$$

Percentage of correct predictions overall.

#### Precision
$$
\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}
$$

Of documents flagged as plagiarized, how many actually were? (Prevents false accusations)

#### Recall
$$
\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}
$$

Of actual plagiarized documents, how many were caught? (Detection rate)

#### F1-Score
$$
\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}
$$

Harmonic mean of precision and recall. Balanced metric for imbalanced problems.

### Current Performance

**System Metrics** (from `test_evaluation.py`):
```
Accuracy:  100%  ✓ Perfect classification
Precision: 1.0   ✓ No false positives
Recall:    1.0   ✓ All plagiarism detected
F1-Score:  1.0   ✓ Perfectly balanced
```

**Interpretation**: System correctly identifies all plagiarism cases without false accusations.

---

## Testing & Validation

### Test Suite Architecture

```
test_evaluation.py
├── Generate/Mock test data
├── Call Flask API endpoints
├── Collect predictions
├── Calculate metrics (accuracy, precision, recall, F1)
└── Generate performance report
```

### Running Tests

```bash
# Start Flask server (in one terminal)
python app.py

# Run tests (in another terminal)
python test_evaluation.py
```

### Expected Output

```
======================================================================
--- SEN501 Group 5: FINAL PERFORMANCE REPORT ---
Plagiarism Detection System - Ready for FUTA Submission
======================================================================

📊 CORE METRICS:
   Accuracy:  100%  ✓ Every pair was correctly identified
   Precision: 1.0   ✓ No original work falsely flagged as plagiarism
   Recall:    1.0   ✓ All plagiarism instances were detected
   F1-Score:  1.0   ✓ Perfect balance - System is robust & fair

🎯 WHY F1-SCORE IS CRITICAL:
   • False Positives: Wrongly accusing students of plagiarism
   • False Negatives: Allowing plagiarized papers to pass
   • F1-Score ensures BOTH fairness AND thoroughness

📋 DETAILED CLASSIFICATION REPORT:
              precision  recall  f1-score support
    Original       1.00    1.00      1.00       5
  Plagiarized      1.00    1.00      1.00       5
       accuracy                      1.00      10

======================================================================
✅ SYSTEM STATUS: READY FOR SUBMISSION
======================================================================
```

---

## Configuration Guide

### Key Parameters

#### 1. Threshold Adjustment

**File**: `app.py` (line 23)

```python
THRESHOLD = 20.0  # Current value
```

**How to adjust**:
- **Increase** (e.g., 25): More conservative, fewer plagiarism flags (↓ false positives, ↑ false negatives)
- **Decrease** (e.g., 15): More aggressive, more plagiarism flags (↑ false positives, ↓ false negatives)

**Recommended range**: 15-25 for academic use

#### 2. N-gram Range Modification

**File**: `app.py` (line 32)

```python
vectorizer = TfidfVectorizer(ngram_range=(2, 3))
```

| Range | Detection | False Positives | Use Case |
|-------|-----------|-----------------|----------|
| (1,1) | Weakest | High | Quick screening |
| (1,2) | Moderate | Moderate | Balanced |
| (2,3) | Current | Low | Strict enforcement |
| (2,4) | Strongest | Very low | Copy-paste detection |

#### 3. Server Configuration

**File**: `app.py` (line 56)

```python
app.run(debug=True, port=5000)
```

**For Production**:
```python
app.run(debug=False, host='0.0.0.0', port=8000)
```

---

## Limitations & Future Work

### Current Limitations

❌ **Cannot detect**:
- Paraphrased plagiarism (reworded content)
- Conceptual plagiarism (different words, same idea)
- Translated plagiarism (from other languages)
- Patchwork plagiarism (multiple small copied sections)

### Recommended Enhancements

1. **Semantic Similarity** (High Priority)
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   embeddings = model.encode(text)  # Semantic vectors
   ```
   Catches paraphrased plagiarism missed by TF-IDF.

2. **Hybrid Scoring**
   ```python
   final_score = (tfidf_score * 0.4) + (semantic_score * 0.6)
   ```

3. **Plagiarism Highlighting**
   ```python
   from difflib import SequenceMatcher
   matches = SequenceMatcher(None, text1, text2).get_matching_blocks()
   ```
   Return which sections matched.

4. **Database Comparison**
   Compare against corpus of existing papers (requires indexing infrastructure).

---

## Deployment Checklist

- [ ] Replace `debug=True` with `debug=False`
- [ ] Set appropriate `THRESHOLD` based on real test data
- [ ] Add input validation (file size limits, format checks)
- [ ] Implement rate limiting (prevent API abuse)
- [ ] Add logging for audit trail
- [ ] Use HTTPS in production
- [ ] Add authentication/API keys
- [ ] Monitor performance and false positive rates

---

## References

- TF-IDF: [scikit-learn documentation](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- Cosine Similarity: [scikit-learn metrics](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
- N-grams: [NLP Basics](https://en.wikipedia.org/wiki/N-gram)
- Plagiarism Detection: [Academic Integrity](https://en.wikipedia.org/wiki/Plagiarism#Detection)

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Maintained By**: SEN501 Group 5
