
import time
import urllib2
from BeautifulSoup import BeautifulSoup

"http://gatherer.wizards.com/Pages/Search/Default.aspx?output=checklist&action=advanced&set=[%22Eighth+Edition%22]"

if __name__ == "__main__":
    page = urllib2.urlopen("http://gatherer.wizards.com/Pages/Search/Default.aspx?output=checklist&action=advanced&set=[%22Eighth+Edition%22]").read()
    soup = BeautifulSoup(page)

    for a in soup.findAll("a", attrs={"class":"nameLink"}):
        name = a.string
        href = a["href"]

        if href.startswith("../Card/Details.aspx?multiverseid="):
            multiverseid = href[len("../Card/Details.aspx?multiverseid="):]

            image = urllib2.urlopen('http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=' + multiverseid + '&type=card').read()
            f = open(name + ".jpg", "w") 
            f.write(image)
            f.close()

            time.sleep(5)

            print (name, multiverseid)

