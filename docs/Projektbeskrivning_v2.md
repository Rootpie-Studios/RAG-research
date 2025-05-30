## **Projektbeskrivning: Utvärdering av Embeddingmodeller för Svensk Text**

### **Bakgrund och Mål**

Vi vill undersöka och förbättra hur embeddingmodeller (AI-modeller som omvandlar text till numeriska vektorer för sök och matchning) fungerar för svenska data. Målet är att identifiera och utvärdera metoder som ökar träffsäkerheten vid sökning efter svar i svenska dokument – med fokus på praktiskt användbara tekniker. Vi vill också tydligt kunna mäta hur tillförlitliga dessa tekniker är genom att använda etablerade klassificeringsmått såsom **precision** och **recall**.

### **Metod**

#### **1\. Datainsamling & Facit**

* Samla in ca 100 PDF-dokument på svenska.

* Skriv cirka 1000 frågor där svaret på varje fråga finns i texterna.

* För varje fråga: spara vilket PDF-dokument, sida och stycke som innehåller svaret (facit).

#### **2\. Databashantering och Embeddings**

* Dela upp PDF:erna i korta textstycken (t.ex. 512 tokens).

* Generera embeddings (vektorer) för varje stycke med OpenAI’s embeddingmodell (länk).

* Spara vektorer och metadata (PDF, sida, stycke, text) i en vektordatabas som t.ex. Qdrant.

#### **3\. Baseline och Utvärdering**

* Baseline: dela upp texten rakt av i jämna block om 512 tokens.

* Vid utvärdering:

  * Kör embedding på frågan.

  * Hämta närmaste grannar från vektordatabasen.

  * Kontrollera om någon av dessa innehåller det förväntade svaret.

* **Accuracy** \= antal lyckade träffar / (lyckade \+ misslyckade försök)

### **Utökad Mätning: Precision, Recall och Klassificering av RAG-resultat**

För att ge en mer nyanserad bild av modellernas användbarhet i verkliga tillämpningar vill vi mäta:

* **Precision**: andelen träffar som faktiskt var relevanta.

* **Recall**: andelen relevanta träffar som faktiskt hittades.

För detta krävs att vårt RAG-system kan ge ett "nej, inget relevant hittades"-resultat, vilket ger oss möjlighet att definiera:

* **True Positive (TP)**: RAG returnerar ett eller flera stycken, och det korrekta dokumentet finns med.

* **False Positive (FP)**: RAG returnerar stycken, men inget är korrekt.

* **False Negative (FN)**: RAG returnerar tomt resultat, trots att ett korrekt svar finns.

* **True Negative (TN)**: RAG returnerar tomt resultat, och inget korrekt svar finns.

Vi inför därför en **tröskel** för likhet (likhetsmått på embeddingnivå) – om inga dokumentstycken passerar denna tröskel anses resultatet vara tomt. Detta möjliggör meningsfull utvärdering av recall/precision.

### **Fördjupad Undersökning / Metodutveckling**

APL-studenterna får utforska följande förbättringar:

#### **1\. Textindelning och Indexering**

* 1.1 Dela upp texten smartare – utgå från stycken, rubriker och meningar.

* 1.2 Låt en LLM generera frågor eller beskrivningar av varje stycke som lagras i databasen.

#### **2\. Frågeförbättring**

* Använd en LLM för att förbättra frågorna genom omskrivning, kontextualisering eller berikning.

#### **3\. Utökad Sökning**

* Hämta t.ex. topp-10 närmaste grannar istället för bara den närmaste, för att öka recall.

#### **4\. Reranking**

* Använd rerankers (LLM eller annan metod) för att förbättra träfflistan utifrån kontext och semantik.

#### **5\. Alternativa Embeddingmodeller**

* Jämför resultat från olika modeller, t.ex. multilingual-e5-large-instruct från Huggingface.

### **Förväntad Leverans**

* Vektordatabas med embeddingar och metadata från PDF:erna.

* Kod och dokumentation av experiment, metodik och mätresultat (inkl. precision/recall/accuracy).

* Rekommendationer om bästa metoder för svensk textanalys och sök.

