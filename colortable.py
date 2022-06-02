import csv

class Colors:
    def __init__(self, color_file):
        self.table = {}
        with open(color_file) as f:
            f.readline()
            reader = csv.reader(f)
            for row in reader:
                self.table[row[0].lower()] = row[1]

    def lookup(self, color_name):
        parsed = color_name.lower().strip()
        if parsed in self.table:
            return self.table[parsed]
