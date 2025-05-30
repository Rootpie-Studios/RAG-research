# Documentation Step 1: Data Creation

## **Baseline**

When creating the baseline for the later improvement we agreed to keep the answers short. Here are a few examples of what the questions and answers look like at the very beginning of the project:

```
[[questions]]
id = "RN022"
question = "När beslutade regeringen att inhämta Lagrådets yttrande över lagförslaget?"
answer = "Den 22 juni 2023"
difficulty = "easy"
category = "education"
[[questions.files]]
file = "2023_24_UbU6_20231211104325_Publicering.pdf"
page_numbers = [5]


[[questions]]
id = "RN023"
question = "Vad var syftet med Läromedelsutredningen som tillsattes 2019?"
answer = "Att bland annat föreslå hur statens roll bör se ut när det gäller läromedel i svensk skola."
difficulty = "easy"
category = "education"
[[questions.files]]
file = "2023_24_UbU6_20231211104325_Publicering.pdf"
page_numbers = [29]


[[questions]]
id = "RN024"
question = "Vad anser undertecknarna är angeläget att regeringen fortsätter med?"
answer = "Att säkerställa en god och likvärdig tillgång till läromedel av hög kvalitet på alla skolor."
difficulty = "easy"
category = "education"
[[questions.files]]
file = "2023_24_UbU6_20231211104325_Publicering.pdf"
page_numbers = [29]
```
The answers are kept short on purpose.




## **Prompts**

These are examples of prompts we use to generate questions, answers and to put
them in the correct structure.

Paulo:</br>
This is the prompt that I use (works ok):
```
Du är en avancerad AI-assistent specialiserad på dokumentanalys och frågeextraktion. 
Ditt mål är att identifiera explicita och implicita frågor som kan besvaras direkt från innehållet i ett dokument. Skapa 12 stycken frågor. 
För varje fråga: tillhandahåll ett svar i form av ett citat från texten. 
Citatet från texten skall vara identisk med det från dokumentet. 
**Utdataformat (TOML - liknande ChromaDB-struktur):** 
Din utdata ska vara i TOML-format, strukturerad för att efterlikna en samling frågor och deras associerade metadata (svar, källfiler, sidnummer). 
**För varje identifierad fråga, tillhandahåll följande TOML-struktur:**

toml:

[[questions]]
id = "unikt_fråge_id_N"                     # En unik identifierare för frågan (börja med siffran i exemplet.)
question = "Den fullständiga texten av den identifierade frågan på svenska."
answer = "Det citerade svaret som finns i dokumentet."
difficulty = "easy"                         # Eller "medium" eller "hard"  baserat på hur lätt svaret är att hitta.
category = "physics" 

# Kapslad tabell för fil- och sidinformation
[[questions.files]]
file = "dokument_namn_eller_id.pdf"         # Identifieraren för dokumentet där svaret finns. Anvend filnamnet i exemplet. 
page_numbers = [sidnummer_1, sidnummer_2]   # En array med sidnummer där svaret finns. Första sidan är det som är angivet i exemplet.
```

Exempel:
```
[[questions]]
id = "PAV257"                    # börja med denna siffra
question = "Hur ofta utkommer Tidskrift för matematik och fysik?"
answer = "Tidskriften udkommer med ett hafte om ungefär tre ark hvarannan mânad."
difficulty = "medium"
category = "mathematics"         # Använd denna. 

[[questions.files]]
file = "Undervisningsmiljo.pdf"  # Använd detta filnamn.
page_numbers = [1]               # Första nummer i dokumentet uygå från detta. Ignorera sidnummer. 
```

Här är texten:


We are working on creating questions and answers taken from PDF with SWedish text.
This will form the baseline data that will use in the project. The goal is to use
the data as a baseline and improve upon it as we go along.

The README.md file shall contain the complete documentation of the steps that we
have finished. At the moment we are working on creating data. One this step is
completed the documention of this step will be added to README.md.

It is important that make sure that every PDF document has a unique file name.
Some sources rename the files to the same name when you download a file. In these
cases we have to change the file names so they are unique.
