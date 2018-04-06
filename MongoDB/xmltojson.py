from lxml import etree
import json

def results(iter,key,value='string'):
    if value =='string':
        return {key:element.text for element in iter}
    elif value =='tuple':
        return {key:[element.text for element in iter]}
    else:
        pass

articleskeys=[('author','tuple'),('title','string'),('pages','string'),('year','string'),
              ('volume','string'),('journal','string'),('url','string'),('ee','string'),
              ('number','string')]

def json_iterator(iterator,articleskeys):
    article_results={}
    for i in articleskeys:
        article_results.update(results(iter=iterator.findall(i[0]),key=i[0],value=i[1]))
    return article_results


def main():
    context = etree.iterparse('dblp_small.xml', dtd_validation=True, load_dtd=False,events=('start', 'end'),
                              encoding='ISO-8859-1',tag=["inproceedings","article","incollection"], html=True)
    iterator = iter(context)
    file=open('final_results2.json', 'w')
    for event, element in iterator:
        if event == 'start':
            results=json_iterator(element,articleskeys)
            results.update({'type':element.tag})
            json.dump(results, file)
            file.write('\n')
            if element.getprevious() is not None:
                #we saved memory.
                del element.getparent()[0]

        elif event == 'end':
            #we saved memory.
            element.clear()
    file.close()
if __name__ == '__main__':
    main()