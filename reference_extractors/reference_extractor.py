class ReferenceExtractor:
    # Die großen Unterschiede in der URL-Struktur von z.B. Wikipedia-Seiten erfordert, dass wir Seitenspezifische Extraktoren 
    # implementieren. Dies soll eine Art Interface hierfür darstellen.
    """Interface for Reference-Extractors
    """
    # More specific type hinting led to errors, unfortunately...
    def __call__(self, html:str) -> set:
        """Extracts a specific set of references from a html document

        Args:
            html (str): Html from which references should be extracted

        Returns:
            list[str]: List of references
        """
        pass