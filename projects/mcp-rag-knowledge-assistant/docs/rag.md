# Retrieval-Augmented Generation
RAG grounds a language model in your own documents: split documents into chunks, index them, retrieve the most relevant chunks for a question and pass them to the model as context.
Good chunking keeps paragraphs intact and adds overlap. Answers should cite the source chunk so users can verify claims.
Retrieval quality is measured offline with recall at k on a labelled question set.
