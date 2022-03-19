import string
from turtle import onclick
from reference_extractors.reference_extractor import ReferenceExtractor
import re

# Known Bug: For unknown reasons, sometimes Wikiarticles are created with urls from this source.
# Said URLs, for unknown reasons, do not include a protocol extension such as ' https:// '
# It is not reliably repeatable, but seems to happen at random.

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

        # These Keywords (In the german wikipedia space ) signal internal references to Kategorypages, Impressum etc.
        only_article_refs = filter(lambda ref: not re.match(r'/wiki/((Datei)|(Spezial)|(Kategorie)|(Wikipedia)|(Hilfe)|(Portal)):.*?', ref), wikipediarefs)
        # Using separate collections, as the use of one set was the most likely to be causing the strange Bug described above.g
        result_set = set()
        for ref in only_article_refs:
            # Turn all into absolute paths according to assumption of german wikipedia.
            if not ref.startswith("https://de.wikipedia.org"):
                result_set.add("https://de.wikipedia.org" + ref)
        return result_set