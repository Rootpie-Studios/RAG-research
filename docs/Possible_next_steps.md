*When trying new stuff, try to only change one variable at a time if possible. For easier comparison.*

**Parser**:
  + Try different ones. (Which ones?)
      - Different strategies within each parser.

**Chunking**:
  + Try different chunk sizes. (How should the text be chunked up?)

**Embeddings**:
  + Embedding models are trained on specific tokenizer.
    
  + Try different models. (Which ones?)
  
  + Fine-tune a model.

  + Doing something like:
    ```python
    from transformers import AutoTokenizer, AutoModel
    import torch
    
    tokenizer = AutoTokenizer.from_pretrained("your-model")
    model = AutoModel.from_pretrained("your-model")
    
    def get_embedding(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    ```
**Tokens**:
  + Needs to work with embedding model. Embedding models are trained on tokenizers.
  
  + If custom tokens -> custom embeddings, otherwise vector space can break or be misaligned.

**Adding Context**:
  + Let LLM write 10 questions (and/or descriptions) of each chunk in database. Let them create a space.
    Now 10 embeddings point to the same chunk, increasing the cross-section of the document being found.
    And adding both questions and descriptions could be benifitial.
