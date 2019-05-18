#basic class-based tkinter template from 
#https://stackoverflow.com/a/17470842 
import tkinter as tk
import receipt2json as receipt
from PIL import Image, ImageTk

COLOR_KEY = {
        'item':'#e5ffcc',
        'date':'#ffffcc',
        'none':'#e0e0e0',
        'head':'#ccccff',
        'foot':'#ccccff',
        'errr':'#ffcccc',
        'coup':'#ccffff',
        'tsum':'#cce5ff',
        'fsum':'#ffe5cc',
    }

BIG_FONT = '-*-lucidatypewriter-medium-r-*-*-*-120-*-*-*-*-*-*'
SMALL_FONT = '-*-lucidatypewriter-medium-r-*-*-*-100-*-*-*-*-*-*'

class Datapane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent,width=280)
        self.parent = parent
        self.pack_propagate(0)

        self.data_list = tk.Listbox(self,# width=15,
                font=BIG_FONT
                )
        self.data_list.pack(side='top', fill='both', expand=True)
        
        self.active_price = tk.StringVar()
        self.active_item = -1
        self.price_entry = tk.Entry(self, textvariable=self.active_price,
                width = 7,
                font=BIG_FONT)
        self.price_entry.pack(side='left')

        self.update_bt = tk.Button(self, text='Update Price',
                font=SMALL_FONT,
                command=self.update_price)
        self.update_bt.pack(side='left')

        self.sum_str = tk.StringVar()
        self.sum_label = tk.Label(self, textvariable=self.sum_str,
                font=BIG_FONT)
        self.sum_label.pack(side='left')

        self.save_bt = tk.Button(self, text='Save List', state=tk.DISABLED,
                font=SMALL_FONT)
        self.save_bt.pack(side='right')

    def update_price(self):
        '''
        get the selection index
        if selection index == self.active_item then update the price
         in self.parsed_lines and update the line at selection index
        else pull price from self.parsed_lines and put in self.price_entry
        '''
        index = self.data_list.curselection()[0]
        #print(index)
        #print(self.active_item)
        if index == self.active_item:
            price = int(self.active_price.get())
            tag, item = self.parsed_lines[index]
            if type(item) is tuple:
                name, _, category = item
                self.parsed_lines.update({index: (tag, (name, price, category))})
                #self.data_list.delete(index)
                self.update_line(index, *self.parsed_lines[index])
                self.check_receipt()
        else:
            self.active_item = index
            _, item = self.parsed_lines[index]
            if type(item) is tuple:
                _, price, _ = item
                self.active_price.set(str(price))

    def parse_file(self, path='./img'):
        img_path = self.parent.filepane.file_str.get()
        self.data_list.delete(0,tk.END)

        lines = receipt.tesseractImage(path + '/' + img_path).splitlines()
        self.parsed_lines = receipt.parseByCategory(lines)

        self.update_pane()

    def update_line(self,idx,tag,line):
        if type(line) is tuple:
            item = ' ## '.join([str(i) for i in line])
        else: item = str(line)
        line_entry = ' '.join((str(idx).rjust(4),tag,item))

        while self.data_list.size() < idx:
            self.data_list.insert(tk.END, '')

        if self.data_list.get(idx) != '':
            #print('update ',self.data_list.get(idx))
            self.data_list.delete(idx)
        self.data_list.insert(idx, line_entry)
        self.data_list.itemconfig(idx, background=COLOR_KEY[tag])

    def update_pane(self):
        self.balance_idx = -1
        for idx, (tag, line) in self.parsed_lines.items():
            self.update_line(idx, tag, line)
            if tag == 'tsum' or tag == 'fsum':
                self.balance_idx = idx
        self.check_receipt()

    def check_receipt(self):
        if self.balance_idx == -1:
            return

        price_sum = 0
        for idx, (tag, line) in self.parsed_lines.items():
            if type(line) is tuple and tag == 'item':
                _, price, _ = line
                price_sum += price
        _, entry = self.parsed_lines[self.balance_idx]
        name, total, cat = entry
        if price_sum == total:
            self.update_line(self.balance_idx, 'tsum', entry)
        else:
            self.update_line(self.balance_idx, 'fsum', entry)
        self.sum_str.set('CURRENT SUM: '+str(price_sum))
 
class Fileops(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.refresh_bt = tk.Button(self, text='Refresh File List',
                font=SMALL_FONT)
        self.read_bt = tk.Button(self, text='Read Selected File',
                font=SMALL_FONT,
                command=self.read_file)
        self.parent = parent
        #read_bt.bind('<Button-1>', parent.filepane.update_view())

        self.readall_bt = tk.Button(self, text='Read All',
                font=SMALL_FONT)
        self.history_ch = tk.Checkbutton(self, text='Ignore history.csv',
                font=SMALL_FONT)

        self.refresh_bt.pack(side='left')
        self.read_bt.pack(side='left')
        self.readall_bt.pack(side='left')
        self.history_ch.pack(side='left')
        #.pack(side='left')

    def read_file(self):
        self.parent.filepane.update_view()
        self.parent.datapane.parse_file()

class Filepane(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.pack_propagate(0)

        files_str = tk.StringVar(); files_str.set(self.read_files())
        self.file_str = tk.StringVar(); 
        self.file_list = tk.Listbox(self, selectmode=tk.BROWSE, 
                listvariable=files_str,
                font=SMALL_FONT)
        self.file_list.activate(0)
        self.file_str.set(self.file_list.get(tk.ACTIVE))

        self.file_view = tk.Label(self)
        self.file_label = tk.Label(self, textvariable=self.file_str,
                font=BIG_FONT)
        self.read_image(self.file_view,self.file_str.get())
        
        self.file_list.pack(side='top', fill='x')
        self.file_label.pack(side='top')
        self.file_view.pack(side='top')

    def read_files(self, path='./img'):
        new_imgs, old_imgs = receipt.findImages(path)
        new_imgs = [i.replace(' ','\\ ') for i in new_imgs]
        old_imgs = [i.replace(' ','\\ ') for i in old_imgs]
        img_str = ' '.join(new_imgs + old_imgs)
        return img_str

    def read_image(self, img_widget, filename, path='./img'):
        if filename is not None:
            image = Image.open(path + '/' + filename)
            image.thumbnail((400,800))
            photo = ImageTk.PhotoImage(image)
            img_widget.config(image=photo)
            img_widget.image = photo

    def update_view(self):
        #print(self.file_list.get(tk.ACTIVE))
        self.file_str.set(self.file_list.get(tk.ACTIVE))
        self.read_image(self.file_view,self.file_str.get())

class FilepaneApplication(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.filepane = Filepane(self)
        self.fileops = Fileops(self)
        self.datapane = Datapane(self)

        self.fileops.pack(side="top", fill="x")
        self.datapane.pack(side="right", fill="both", expand=True)
        self.filepane.pack(side="left", fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    FilepaneApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
