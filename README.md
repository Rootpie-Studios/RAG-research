# RAG-research
RAG for swedish documents

Source data for the project: [https://drive.google.com/drive/folders/1_epDuB8VUgaXHcu14uKPMTi8DXU9XLxm?usp=sharing](https://drive.google.com/drive/folders/1_epDuB8VUgaXHcu14uKPMTi8DXU9XLxm?usp=sharing)

## **Background and Goal**
We want to investigate and improve how embedding models (AI models that convert text into numerical vectors for search and matching) perform on Swedish data. The goal is to identify methods that increase accuracy when searching for answers in Swedish documents.


Chunk size: 512 tokens max.


## **Questions structure**

```toml
[[questions]]
id = "PMCSKOLVERKET002"
question = "Hur många elever i grundskolan omfattas av ett åtgärdsprogram läsåret 2024/25?"
answer = "Läsåret 2024/25 omfattas 6,7 procent av eleverna i grundskolan av ett åtgärdsprogram, vilket motsvarar knappt 73 200 elever"
difficulty = "easy"
category = "education"

[[questions.files]]
file = "pdf1323q9.pdf"
page_numbers = [4, 10]
```

The id is the id of the person who created the question.

Difficulty refers to the difference between the phrasing of the question and answer. It’s not about the difficulty of the subject.
