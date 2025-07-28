# 🚀 Intelligent Document Analyst  

**Transform Unstructured PDFs into Actionable Insights**  

## 🔍 Overview  
The **Intelligent Document Analyst** processes PDF documents to extract and prioritize relevant sections based on a **user persona** and their **job-to-be-done**.  

🔹 **Containerized & Efficient** – Runs in Docker, optimized for CPU-only environments.  
🔹 **Semantic Understanding** – Combines AI embeddings with keyword boosting.  
🔹 **Lightweight** – Fast processing with minimal hardware requirements.  

---

## 🛠️ How It Works  

### 📂 **Pipeline Stages**  
1. **Document Ingestion** – Uses PyMuPDF for PDF parsing and text chunking.  
2. **Semantic Query** – Constructs context-aware queries from user inputs.  
3. **AI Ranking** – Leverages `all-MiniLM-L6-v2` for embeddings and relevance scoring.  
4. **Output Generation** – Ranks results into structured JSON.  

---

## 🛠️ Tech Stack  
- **Model**: `all-MiniLM-L6-v2` (lightweight sentence transformer)  
- **Libraries**: PyMuPDF, Sentence-Transformers, PyTorch (CPU), NumPy  
- **Containerization**: Docker  

---

## 🚀 Quick Start  

### **Prerequisites**  
✅ Docker installed  

### **Run Analysis**  
1. Build the image:  
   ```sh  
   docker build -t intelligent-analyst .  

2. Process documents:
   ```
   docker run --rm \  
  -v "$(pwd)/Collection 1:/app/data" \  
  intelligent-analyst \  
  "data/challenge1b_input.json" > "Collection 1/challenge1b_output.json"  
  ```

