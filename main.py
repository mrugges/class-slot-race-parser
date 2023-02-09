import pandas as pd
import requests
import urllib
from bs4 import BeautifulSoup
import time
from pydantic import BaseModel
from typing import Tuple, Dict, Set, List


class SlotParser(BaseModel):

    base_url: str = 'https://everquest.allakhazam.com'
    headers: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    all_classes: Set[str] = {
        "WAR", "PAL", "RNG", "SHD", "MNK", "BRD", "ROG", "BST", "BER", "WIZ", "SHM", "DRU", "NEC", "MAG", "ENC", "CLR"
    }

    all_races: Set[str] = {
        "BAR", "DEF", "DWF", "ERU", "FRG", "GNM", "HEF", "HFL", "HIE", "HUM", "IKS", "OGR", "TRL", "VAH", "ELF"
    }

    def clean_name(self, n):
        return n.rstrip().lower().replace('\'', '').replace('`', '')

    def scrape_item(self, item_name: str) -> Tuple[str, str, str]:
        time.sleep(1)
        url = f'{self.base_url}/search.html?q={urllib.parse.quote(item_name)}'
        print(url)
        res = requests.get(url=url, headers=self.headers)
        # print(res.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        # print(soup.prettify())
        table = soup.find("div", {"id": "Items_t"})

        cur_slot, cur_class, cur_race = '', '', ''

        for link in table.findAll("a"):
            print(link)
            s = link.find("span")
            if s:
                s.extract()

            if self.clean_name(str(link.contents[0])) == self.clean_name(item_name):

                print(link['href'])
                time.sleep(1)
                url = f'{self.base_url}{link["href"]}'
                res = requests.get(url, headers=self.headers)
                soup = BeautifulSoup(res.content, 'html.parser')
                for br in soup.find("td", {"class", "shotdata"}).findAll('br'):
                    txt = br.nextSibling
                    if not cur_slot and "Slot" in txt:
                        cur_slot = txt.split(": ")[1]
                    elif "Class" in txt:
                        cur_class = txt.split(": ")[1]
                    elif "Race" in txt:
                        cur_race = txt.split(": ")[1]

                #print(cur_slot, cur_class, cur_race)
                return cur_slot, cur_class, cur_race

        print(f"ERROR: could not find {item_name}")

    def expand_races(self, lst: List[str]) -> List[str]:
        if 'except' not in lst:
            if 'ALL' not in lst:
                return lst
            elif len(lst) > 1:
                raise ValueError(f"{lst} contains more than one class with ALL, and no except")
            else:
                return list(self.all_races)

        to_exclude = lst[lst.index('except') + 1:]
        print(to_exclude)
        rem = self.all_races - set(to_exclude)
        print(rem)
        return list(rem)

    def expand_classes(self, lst: List[str]) -> List[str]:
        """
        ['ALL', 'except', 'CLR', 'DRU', 'MNK', 'SHM', 'BST', 'BER'] =>
        all_classes - set(everything after except)
        ['ALL'] => all_classes
        """
        if 'except' not in lst:
            if 'ALL' not in lst:
                return lst
            elif len(lst) > 1:
                raise ValueError(f"{lst} contains more than one class with ALL, and no except")
            else:
                return list(self.all_classes)

        to_exclude = lst[lst.index('except')+1:]
        print(to_exclude)
        rem = self.all_classes - set(to_exclude)
        print(rem)
        return list(rem)

def main():
    # get all classes ids, along with 1 item name example
    # get all races ids, along with 1 item name example
    # get all slots ids, along with 1 item name example

    # scrape item page for each example item allakhazam
    # first hit the search page: https://everquest.allakhazam.com/search.html?q=Netted+Gloves
    # then click on item name
    # e.g. https://everquest.allakhazam.com/db/item.html?item=1522
    # scrape. e.g.
    # Slot: HANDS
    # Class: ALL
    # Race: ALL

    # populate classes, races and slots as needed

    classes_name_to_id = {
        #'MNK': set()
    }

    class_id_to_name = {
        #'0': set()
    }

    ce = pd.read_csv("class_examples.csv")
    #print(class_examples)




    item_name = "Netted Gloves"
    p = SlotParser()

    class_data = pd.DataFrame(columns=['classes', 'class_name'])
    race_data = pd.DataFrame(columns=['races', 'race_name'])
    slot_data = pd.DataFrame(columns=['slots', 'slot_name'])

    skipped = []
    for race_id, class_id, slot_id, item_name in list(zip(ce['races'], ce['classes'], ce['slots'], ce['n'])):
        try:
            slot_names, class_names, race_names = p.scrape_item(item_name)
            print(race_id, class_id, slot_id, item_name, slot_names.split(), class_names.split(), race_names)

            class_names = p.expand_classes(class_names.split())
            race_names = p.expand_races(race_names.split())
            slot_names = slot_names.split()

            cd = pd.DataFrame(zip([class_id] * len(class_names), class_names), columns=['classes', 'class_name'])
            class_data = pd.concat([class_data, cd]).drop_duplicates()

            rd = pd.DataFrame(zip([race_id] * len(race_names), race_names), columns=['races', 'race_name'])
            race_data = pd.concat([race_data, rd]).drop_duplicates()

            sd = pd.DataFrame(zip([slot_id] * len(slot_names), slot_names), columns=['slots', 'slot_name'])
            slot_data = pd.concat([slot_data, sd]).drop_duplicates()
        except Exception as ex:
            print(f"Error {ex}")
            skipped += [race_id, class_id, slot_id, item_name]

    class_data.to_csv("class_data.csv")
    race_data.to_csv("race_data.csv")
    slot_data.to_csv("slot_data.csv")
    print(skipped)


if __name__ == '__main__':
    main()

