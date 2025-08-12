# **Evaluation of Embedding Models for Swedish Text**

## **Important Links**

- Documents used in this Project: [RAG-Research-GDrive](https://drive.google.com/drive/folders/1_epDuB8VUgaXHcu14uKPMTi8DXU9XLxm?usp=sharing)
- Our Final Report: [Evaluation of Embedding Models for Swedish Text](docs/RAG_Final_Report.pdf)

## **Background and Goal**

The main goal of this project was to investigate and improve how embedding models
work with Swedish data, focusing on using practical techniques and finding open source
alternatives. To do this, a dataset of around 100 Swedish PDF documents was gathered and
approximately 1000 questions were written about these documents. After embedding the
documents and inserting them into a vector database (ChromaDB), the questions were also
embedded, and a query with similarity search was performed for each question. The results
were then compiled and analyzed. Using this workflow, different parsers, embedding models,
and various settings were tested in a systematic way, in an attempt to find improvements.

## **Questions structure**

To Evaluate a RAG Implementation we needed to create a Dataset that contained Questions
and Answers in Swedish with information on what file and page that Q/A data pointed do. We
decided to use TOML structure to generate our Question/Answer Dataset because it is more
Human friendly and easy to see the structure and not have to worry about missing curly brackets
and parenthesis compared to JSON structure or CSV files etc.

The format was decided to look like this:

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

## **Implementation**

In this repo you will find different implementations and tests we did. See each directory and its corresponding `README.md` for more information on `HOW` and `WHAT` was implemented and tested.
