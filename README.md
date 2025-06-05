# RAG-research
RAG for swedish documents

Source data for the project: [https://drive.google.com/drive/folders/1_epDuB8VUgaXHcu14uKPMTi8DXU9XLxm?usp=sharing](https://drive.google.com/drive/folders/1_epDuB8VUgaXHcu14uKPMTi8DXU9XLxm?usp=sharing)

## **Background and Goal**
We want to investigate and improve how embedding models (AI models that convert text into numerical vectors for search and matching) perform on Swedish data. The goal is to identify methods that increase accuracy when searching for answers in Swedish documents.


Chunk size: 512 tokens max.


## **Questions structure**

```toml
[[questions]]
id = "PMCEMB111"
question = "Vad är en 'pipe' i MIPS?"
answer = "För MIPS sker detta i en sk. pipe, eller vilket jag tycker är bättre på ett \"löpande band\"."

difficulty = "easy"
category = "Computer architecture"

[[questions.files]]
file = "Kap1.pdf"
page_numbers = [2]
```

The id is the id of the person who created the question.

Difficulty refers to the difference between the phrasing of the question and answer. It’s not about the difficulty of the subject.
