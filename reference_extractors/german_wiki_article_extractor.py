import string
from turtle import onclick
from reference_extractors.reference_extractor import ReferenceExtractor
import re


class GermanWikipediaArticleReferenceExtractor(ReferenceExtractor):
    """Extraktor für Artikel-Referenzen auf das deutsche Wikipedia 
    """
    def __call__(self, html: str) -> set:
        """Extrahiert alle Referenzen, die auf einen de.wikipedia.org artikel verweisen.
        Vorsicht: Verweise auf den selben Host werden als Verweis auf de.wikipeia.org interpretiert.


        Args:
            html (str): html in dem Referenzen gefunden werden sollen

        Returns:
            set[str]: referenzen auf Artikel
        """
        # No hashtags, used in wikipedia for internal referencing
        wikipediarefs =  re.findall(r'<a\s+href="((?:(?:https?://)?de.wikipedia.org)?/wiki/(?:[^#"\s]|)+?)"[^<>]*', html)
        # Fürs erste wird sich auf das deutsche Wikipedia beschränkt. Internationale Artikel könnten noch in neuer Klasse implementiert werden.
        # Filtere hier für Wikipedia DE spezifische interne Seiten für Dateien, Kategorien etc. heraus.
        only_article_refs: set[str] = set(filter(lambda ref: not re.match(r'/wiki/((Datei)|(Spezial)|(Kategorie)|(Wikipedia)|(Hilfe)|(Portal)):.*?', ref), wikipediarefs))
        for ref in only_article_refs:
            # Turn all into absolute paths according to assumption of german wikipedia.
            if not ref.startswith("https://de.wikipedia.org"):
                only_article_refs.add("https://de.wikipedia.org" + ref)
                only_article_refs.remove(ref)

        return only_article_refs