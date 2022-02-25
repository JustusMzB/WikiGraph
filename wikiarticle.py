import requests
import re
import time

class WikiArticle:
    '''
        Encapsulation of the Article, with default implementation. Alternatives could store the html permanently
        instead of only storing the reference.
    '''
    def __init__(self, url, session = None) -> None:
        """Initializes the WikiArticle

        Args:
            url (str): Url to the represented wikipedia article
            session (requests.Session, optional): Optional: The Request Session within which the articles contents are retrieved. Accelarates mass creation of WikiArticle objects. Defaults to None.
        """
        self.session = session
        self._html_cache = None
        self.url = url
        self._html_cache = self.html      
        self.title = re.search(r'<h1 id="firstHeading" .*?>(.*?)</h1>', self.html).group(1)
    @property
    def html(self):
        """Html of the article page

        Returns:
            str: Html of the wikipedia page
        """                                                                                                                                         
        if self._html_cache:
            return self._html_cache
        elif self.session != None:
            response = self.session.get(self.url)
        else:
            response = requests.get(self.url)
        return response.content.decode("UTF_8")
    @property
    def references(self):
        """Contains all references, attemptedly filtered to only include references to articles.

        Returns:
            list[str]: reference urls to wikipedia articles referenced within this one.
        """
        html = self.html
        # No hashtags, used in wikipedia for internal referencing
        validtags =  re.findall(r'<a href="/wiki/[^#]*?">', html)
        # Fürs erste wird sich auf das deutsche Wikipedia beschränkt. Internationale Artikel sind auf jeden Fall noch in planung.
        # internationaltags = re.findall(r'<a href="https://..\.wikipedia.org/wiki/.*?">', html)
        full_references = set()
        for tag in validtags:
            #todo: Filter out references where the link ends on a data ending.
            link_with_end =  re.search(r'/wiki/.*?"', tag).group(0)
            base_url = re.search(r'https://..\.wikipedia.org', self.url).group(0)
            link_with_end = link_with_end.replace('"', '')
            full_references.add(base_url + link_with_end)
        #for tag in internationaltags:
            #link = re.search(r'"https://.*?"', tag).group(0)
            #link.replace('"', '')
            #full_references.append(link)

        #Vermutung: Bei Baumerstellung wird das HTML nur zwei mal benötigt, deshalb kann das cached html jetzt
        #für die garbage collection freigegeben werden.
        self._html_cache = None
        return full_references
    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, WikiArticle) and self.url == __o.url
    def __ne__(self, __o: object) -> bool:
        return not self == __o
    
if __name__ == "__main__":
    """Test is run if the module is executed.
    """
    session = requests.Session()
    article =WikiArticle("https://de.wikipedia.org/wiki/Harry_Potter_%28Filmreihe%29", session=session)
    start = time.time()
    references = article.references
    for reference in article.references:
        WikiArticle(reference, session)
    ex_time = time.time() - start
    print(f"took {ex_time} to get {len(references)} refs and create articles.")
    