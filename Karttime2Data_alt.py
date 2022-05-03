import cv2 
import numpy as np
import easyocr
#from matplotlib import pyplot as plt
import re
import csv
import pprint 
import os


class Kartzeiten:

    def __init__(self, path):

        # Erstellung einer GUI
        self.pic_path = path
        self.save_path = self.pic_path.replace(os.path.basename(self.pic_path), "")

        self.pp = pprint.PrettyPrinter(indent=4)
        self.header = ['LAP', 'Time', 'Kart']

        self.image = cv2.imread(self.pic_path)
        reader = easyocr.Reader(['en'], gpu=True)
        self.result = reader.readtext(self.image)

        for detection in self.result:
            top_left = tuple([int(val) for val in detection[0][0]])
            bottom_right = tuple([int(val) for val in detection[0][2]])
            time_text =  detection[1]
            confidence_text = str(round(detection[2],2)) 
            font = cv2.FONT_HERSHEY_SIMPLEX
           
            self.image = cv2.putText(self.image, time_text, top_left, font, 0.5,  (255,0,0), 1, cv2.LINE_AA)
            self.image = cv2.putText(self.image, confidence_text, bottom_right, font, 0.3,  (0,255,0), 1, cv2.LINE_AA)

        self.Kart_list      = []
        self.valid_laps     = []
        self.invalid_laps   = []
        self.Tabelle_Kartlap = []
        self.lap_time_list = []

        existing_laps = []        

        self.fastest_lap_valid = None
        self.fastest_lap_valid = None
        self.lap_of_change_Kart = None
        self.sek01 = None
        self.sek02 = None
        self.sek03 = None

        self.s_ms    = True
        self.m_s_ms  = True 

        # Suchen der Anzahl an Karts
        for kart in self.result:
            kart_num = re.search('.*(K.*)(.*|[\s])([0-9]{1,2}|Z)', kart[1])
            if kart_num:
                Kart = f'{kart_num.group(0)}'
                Kart = Kart.replace(' ', '')
                if Kart not in self.Kart_list:
                    #print(f'found:   {Kart}')
                    re_kartnum = re.search('([0-9]{1,2}|Z)', Kart)
                    if re_kartnum.group(1) == 'Z':
                        self.Kart_list.append(f'Kart 7')
                    else:
                        self.Kart_list.append(f'Kart {re_kartnum.group(1)}')

        self.Kart_list = [kart for n,kart in enumerate(self.Kart_list) if kart not in self.Kart_list[:n]]
        # Wenn kein Kart gefunden wurde, wird "your Kart" erstellt 
        if not self.Kart_list:
            Kart = 'Kart'
            self.Kart_list.append(Kart)


        # Auswerten der Runden und Zeiten
        if len(self.Kart_list) == 1:
            for time in range(len(self.result)):
                
                laptime_row  = self.result[time][1]
                lap_row = self.result[time-1][1]

                # LapTime [m_s_ms]
                laptimes_m_s_ms = re.search('([0-9]{2}).([0-9]{2}).([0-9]{2,3}).*', laptime_row)

                # LapTime [s_ms] 
                laptimes_s_ms = re.search('([0-9]{2}).([0-9]{2,3}).*', laptime_row)
                # Lap
                lap_re = re.search('([0-9]{1,3})',  lap_row)
            
                if self.m_s_ms and laptimes_m_s_ms and lap_re:
                    self.s_ms = False
                    laptime = f'{laptimes_m_s_ms.group(1)}:{laptimes_m_s_ms.group(2)},{laptimes_m_s_ms.group(3)}'
                    lap = lap_re[0]
                    lap_laptime = {self.header[0] : int(lap), self.header[1] : laptime, self.header[2] : Kart}
                    if lap != '00' and int(lap) not in existing_laps:
                        self.valid_laps.append(lap_laptime)
                    else:
                        self.invalid_laps.append(lap_laptime)
                    existing_laps.append(int(lap))
                    continue     

                elif self.s_ms and laptimes_s_ms and lap_re:
                    self.m_s_ms = False
                    laptime = f'00:{laptimes_s_ms.group(1)},{laptimes_s_ms.group(2)}'
                    lap = int(lap_re[0])
                    lap_laptime = {self.header[0]: lap, self.header[1]: laptime, self.header[2] : Kart}
                    if lap != '00' and int(lap) not in existing_laps:
                        self.valid_laps.append(lap_laptime)
                    else:
                        self.invalid_laps.append(lap_laptime)
                    existing_laps.append(lap)
                    continue
            
                else:
                    continue
        
            self.valid_laps.sort(key=lambda x:x[self.header[0]])
            self.invalid_laps.sort(key=lambda x:x[self.header[0]])

            # Fasted und Slowed Lap:
            #---------------------------------------------------------------------------------
            if self.valid_laps:
                self.fastest_lap_valid   = min(self.valid_laps, key=lambda x:x[self.header[1]])
                self.slowest_lap_valid   = max(self.valid_laps, key=lambda x:x[self.header[1]])


            if self.invalid_laps:
                self.fastest_lap_invalid = min(self.invalid_laps, key=lambda x:x[self.header[1]])
            
            if self.valid_laps and self.invalid_laps:
                if list(self.fastest_lap_invalid.values())[1] < list(self.fastest_lap_valid.values())[1]:
                    print(f'the fastest lap was found in the invalid list')
                    print(f'invalid time: {list(self.fastest_lap_invalid.values())[1]}')
                    print(f'valid time  : {list(self.fastest_lap_valid.values())[1]}')

                    print('-'*50)

            self.Laps  = [lap[self.header[0]] for lap in self.valid_laps]
            self.Times = [time[self.header[1]] for time in self.valid_laps]

            self.fastest_time = float(self.fastest_lap_valid['Time'].replace(':', '.').replace(',', ''))
            self.slowest_time = float(self.slowest_lap_valid['Time'].replace(':', '.').replace(',', ''))

            self.Time2Float = [float(time.replace(':', '.').replace(',', '')) for time in self.Times]

            self.ylabel = [y for y in self.Time2Float if y < np.mean(self.Time2Float)*1.3]

        #---------------------------------------------------------------------------------

        elif len(self.Kart_list) > 1:

            num_karts = len(self.Kart_list)
        
            for time in range(len(self.result)):

                laptime_row  = self.result[time][1]
                laptimes_s_ms = re.search('.*([0-9]{2}).*([0-9]{3}).*', laptime_row)
                if laptimes_s_ms:
                    self.lap_time_list.append(f'00:{laptimes_s_ms.group(1)},{laptimes_s_ms.group(2)}')

            idx = 0
            self.Num_Laps_Tabelle = round(len(self.lap_time_list)/num_karts)

            for num, Kart in enumerate(self.Kart_list):
                if idx >= self.Num_Laps_Tabelle:
                    idx = 0
                for lap, time in enumerate(self.lap_time_list):
                    if idx >= self.Num_Laps_Tabelle:
                        break
                    dict_kartlap = {'LAP': round(lap+1), 'Time' : self.lap_time_list[idx*num_karts+num], 'Kart':Kart}
                    self.Tabelle_Kartlap.append(dict_kartlap)
                    idx += 1
                idx += 1
                
            self.Laps_Taballe = [lap['LAP'] for lap in self.Tabelle_Kartlap]
            self.Times = [list(time.values())[1] for time in self.Tabelle_Kartlap]

            self.Kart_Times_Tabelle = []

            for KART in self.Kart_list:
                time_KART = [list(lap.values())[1] for lap in self.Tabelle_Kartlap if list(lap.values())[2] == KART]
                self.Kart_Times_Tabelle.append([float(time.replace(':', '.').replace(',', '')) for time in time_KART])

            self.Time2Float = [float(time.replace(':', '.').replace(',', '')) for time in self.Times]
            self.ylabel = [y for y in self.Time2Float if y < np.mean(self.Time2Float)*1.3]

            self.Laps = [lap for lap in range(1, self.Num_Laps_Tabelle+1)]

            self.idx_min_time_tabelle = []

            for mintime in self.Kart_Times_Tabelle:
                min_time = np.argmin(mintime)
                self.idx_min_time_tabelle.append(min_time)
            
            self.idx_min_time_abs_tabelle = np.argmin(self.lap_time_list)

    def kart_change_dection(self):

        self.sectors = []
        self.Change_Kart = []

        for lapdict in self.valid_laps:
            if float(lapdict['Time'].replace(':', '.').replace(',', '')) > np.mean(self.Time2Float)*2:
                self.Change_Kart.append(lapdict)

        num_of_changes = len(self.Change_Kart)

        self.lap_of_change_Kart = list(map(lambda x : x['LAP'], self.Change_Kart))

        if self.lap_of_change_Kart:

            for laps in self.valid_laps:
                if num_of_changes == 1 and laps['LAP'] != 0:
                    if laps['LAP'] < self.Change_Kart[0]['LAP'] and laps['LAP'] not in self.lap_of_change_Kart:
                        self.sectors.append({'SEKTOR_1' : laps})
                    elif laps['LAP'] not in self.lap_of_change_Kart:
                        self.sectors.append({'SEKTOR_2' : laps})
                elif num_of_changes == 2 and laps['LAP'] != 0 and laps['LAP'] not in self.lap_of_change_Kart:
                    if laps['LAP'] < self.Change_Kart[0]['LAP']:
                        self.sectors.append({'SEKTOR_1' : laps})
                        continue
                    elif self.Change_Kart[0]['LAP'] < laps['LAP'] and laps['LAP'] < self.Change_Kart[1]['LAP'] and laps['LAP'] not in self.lap_of_change_Kart:
                        self.sectors.append({'SEKTOR_2' : laps})
                        continue
                    elif laps['LAP'] not in self.lap_of_change_Kart:
                        self.sectors.append({'SEKTOR_3' : laps})
                    else:
                        print('cannot assign lap in a sectore')
                elif num_of_changes > 2:
                    print('! warning !- to many Kartchanges, please call Kevin Thalmann ...')

            return(self.sectors)

      
    def kart_change_analyse(self):
        
        if len(self.Kart_list) == 1:
            self.sek01 = []
            self.sek02 = []
            self.sek03 = []
            
            KartChanges = self.kart_change_dection()
            if KartChanges:
                Sektoren = sorted(list(set(list(map(lambda x : list(x.keys())[0], KartChanges)))))

                for idx, Sektor in enumerate(Sektoren):
                    for KartChange in KartChanges:
                        if list(KartChange.keys())[0] == Sektor and idx == 0:
                            self.sek01.append(KartChange)
                        elif list(KartChange.keys())[0] == Sektor and idx == 1:
                            self.sek02.append(KartChange)
                        elif list(KartChange.keys())[0] == Sektor and idx == 2:
                            self.sek03.append(KartChange)

                if self.sek01:

                    self.LAP_sek1   = list(map(lambda x : float(list(x.values())[0]['LAP']), self.sek01))
                    self.TIME_sek1  = list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek01))

                    idx_MIN_sek1 = np.argmin(list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek01)))

                    self.min_TIME_sek01  = self.TIME_sek1[idx_MIN_sek1]
                    self.min_LAP_sek01   = round(self.LAP_sek1[idx_MIN_sek1])

                    mean_sek01 = [time for time in self.TIME_sek1 if time < self.min_TIME_sek01*1.2]

                    self.mean_sek01 = round(np.mean(mean_sek01), 3)#
            
                    self.dif_mean_min_sek01 = round(self.mean_sek01 - self.min_TIME_sek01, 3)

        
                if self.sek02:
                    self.LAP_sek2   = list(map(lambda x : float(list(x.values())[0]['LAP']), self.sek02))
                    self.TIME_sek2  = list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek02))

                    idx_MIN_sek2 = np.argmin(list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek02)))

                    self.min_TIME_sek02  = self.TIME_sek2[idx_MIN_sek2]
                    self.min_LAP_sek02   = round(self.LAP_sek2[idx_MIN_sek2])

                    mean_sek02 = [time for time in self.TIME_sek2 if time < self.min_TIME_sek02*1.2]

                    self.mean_sek02 = round(np.mean(mean_sek02), 3)
                    self.dif_mean_min_sek02 = round(self.mean_sek02 - self.min_TIME_sek02, 3)

            
                if self.sek03:
                    self.LAP_sek3   = list(map(lambda x : float(list(x.values())[0]['LAP']), self.sek03))
                    self.TIME_sek3  = list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek03))

                    idx_MIN_sek3 = np.argmin(list(map(lambda x : float(list(x.values())[0]['Time'].replace(':', '.').replace(',', '')), self.sek03)))

                    self.min_TIME_sek03  = self.TIME_sek3[idx_MIN_sek3]
                    self.min_LAP_sek03   = round(self.LAP_sek3[idx_MIN_sek3])

                    mean_sek03 = [time for time in self.TIME_sek3 if time < self.min_TIME_sek03*1.2]

                    self.mean_sek03 = round(np.mean(mean_sek03), 3)
                    self.dif_mean_min_sek03 = round(self.mean_sek03 - self.min_TIME_sek03, 3)

                
        def show_text(self):

            for changelap in self.lap_of_change_Kart:
                print(f'found  a Kart change in Lap : {changelap}')
                print('-'*50)
            else:
                print('there are no Kart changes')
                print('-'*50)
            
            if self.sek01:
                print(f'your fastest time with Kart 1       : {self.min_TIME_sek01} in Lap : {self.min_LAP_sek01}')
                print(f'the meantime with Kart 1            : {self.mean_sek01}')
                print(f'Differenz meantime - fastest time   : {self.dif_mean_min_sek01}')
                print('-'*50)
            if self.sek02:
                print(f'your fastest time with Kart 2       : {self.min_TIME_sek02} in Lap : {self.min_LAP_sek02} ')
                print(f'the meantime with Kart 2            : {self.mean_sek02}')
                print(f'Differenz meantime - fastest time   : {self.dif_mean_min_sek02}')
                print('-'*50)
            if self.sek03:
                print(f'your fastest time with Kart 3       : {self.min_TIME_sek03} in Lap : {self.min_LAP_sek03}')
                print(f'the meantime with Kart 3            : {self.mean_sek03}')
                print(f'Differenz meantime - fastest time   : {self.dif_mean_min_sek03}')
                print('-'*50)


    def show_laps(self):

        if self.valid_laps:
            #self.pp.pprint(self.valid_laps)
            return self.valid_laps

        if self.Tabelle_Kartlap:
            #self.pp.pprint(self.Tabelle_Kartlap)
            return self.Tabelle_Kartlap

    
    def show_fasted_lap(self):
        
        if self.fastest_lap_valid:
            text = f'the fastest lap: {self.fastest_lap_valid}'
            #self.pp.pprint(text)    
            return text
        else:
            print('can not found the fastest lap')
            return None


    def show_picture(self):

        plt.figure(figsize=(12,12))
        plt.imshow(self.image)
        plt.show()

    def export2csv(self):

        if len(self.Kart_list) == 1:
            with open(f"{self.save_path}export_valid_laps.csv", 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = self.header, delimiter=';')
                writer.writeheader()
                for key in self.valid_laps:
                    writer.writerow(key)

            with open(f"{self.save_path}export_invalid_laps.csv", 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = self.header, delimiter=';')
                writer.writeheader()
                for key in self.invalid_laps:
                    writer.writerow(key)
        elif len(self.Kart_list) > 1:
            with open(f"{self.save_path}export_laps.csv", 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = ['Kart', 'LAP', 'Time'], delimiter=';')
                writer.writeheader()
                for key in self.Tabelle_Kartlap:
                    writer.writerow(key)


    def plot_laps(self):
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

        #for kart in self.Kart_list:
        fig = plt.figure(figsize=(16,10))

        if len(self.Kart_list) > 1:
            
            for i, (Time, Kartname, idx_min) in enumerate(zip(self.Kart_Times_Tabelle, self.Kart_list, self.idx_min_time_tabelle)):
                colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g', 'r', 'c', 'm', 'y', 'k']
                plt.plot(self.Laps, Time, 'o-', linewidth=1.5, color=colors[i], label=Kartname)
                plt.vlines(self.Laps[idx_min],0, Time[idx_min], color=colors[i], linewidth=1, label=f"Besttime{Kartname}:  {Time[idx_min]} min")
                plt.text(self.Laps[idx_min]+0.5,  Time[idx_min]-0.0008,   f"Time: {Time[idx_min]}", verticalalignment='center', fontsize=12, color='green', bbox=props)

        elif len(self.Kart_list) == 1:

            plt.plot(self.Laps, self.Time2Float, 'o-', linewidth=1.2, color='gray')
            plt.plot(self.fastest_lap_valid['LAP'], self.fastest_time,'x' ,color='green', linewidth=2)

            if self.sek01:
                plt.plot(self.LAP_sek1, self.TIME_sek1,'-' ,color='blue', linewidth=2, label='Driver 01')
                plt.plot(self.min_LAP_sek01 ,self.min_TIME_sek01 ,'x' ,color='blue', linewidth=2, label=f'Fastest Lap: {self.min_TIME_sek01} min')
                plt.text(self.min_LAP_sek01+0.5,  self.min_TIME_sek01-0.0008,   f"Time: {self.min_TIME_sek01}", verticalalignment='center', fontsize=12, color='green', bbox=props)

                z1 = np.polyfit(self.LAP_sek1[1:], self.TIME_sek1[1:], 1)
                p1 = np.poly1d(z1)
                plt.plot(self.LAP_sek1[1:], p1(self.LAP_sek1[1:]),ls="-.", linewidth=1, label='Trend Driver 01', color='gray')
                
            if self.sek02:
                plt.plot(self.LAP_sek2, self.TIME_sek2,'-' ,color='orange', linewidth=2, label='Driver 02')
                plt.plot(self.min_LAP_sek02 ,self.min_TIME_sek02 ,'x' ,color='orange', linewidth=2, label=f'Fastest Lap: {self.min_TIME_sek02} min')
                plt.text(self.min_LAP_sek02+0.5,  self.min_TIME_sek02-0.0008,   f"Time: {self.min_TIME_sek02}", verticalalignment='center', fontsize=12, color='green', bbox=props)

                z2 = np.polyfit(self.LAP_sek2[1:], self.TIME_sek2[1:], 1)
                p2 = np.poly1d(z2)
                plt.plot(self.LAP_sek2[1:], p2(self.LAP_sek2[1:]), ls="-.", linewidth=1, label='Trend Driver 02', color='gray')

            if self.sek03:
                plt.plot(self.LAP_sek3, self.TIME_sek3,'-' ,color='lightblue', linewidth=2, label='Driver 03')
                plt.plot(self.min_LAP_sek03 ,self.min_TIME_sek03 ,'x' ,color='green', linewidth=2, label=f'Fastest Lap: {self.min_TIME_sek03} min')
                plt.text(self.min_LAP_sek03+0.5,  self.min_TIME_sek03-0.0008,   f"Time: {self.min_TIME_sek03}", verticalalignment='center', fontsize=12, color='green', bbox=props)

                z3 = np.polyfit(self.LAP_sek3[1:], self.TIME_sek3[1:], 1)
                p3 = np.poly1d(z3)
                plt.plot(self.LAP_sek3[1:], p3(self.LAP_sek3[1:]),ls="-.", linewidth=1, label='Trend Driver 03', color='gray')

            if self.lap_of_change_Kart:
                for i, changes in enumerate(self.lap_of_change_Kart):
                    plt.axvline(changes, color='red',ls=':', linewidth=1.5)

                if len(self.lap_of_change_Kart) == 1:
                    plt.hlines(self.mean_sek01, 0, self.lap_of_change_Kart[0], color='lightgray',ls='--', label = f'Meantime Driver 01:  {self.mean_sek01} min')
                    plt.hlines(self.mean_sek02, self.lap_of_change_Kart[0], self.Laps[-1], color='lightgray',ls='--', label = f'Meantime Driver 02:  {self.mean_sek02} min')

                    plt.hlines(self.min_TIME_sek01, 0, self.lap_of_change_Kart[0], color='green',ls='--', linewidth=1)
                    plt.hlines(self.min_TIME_sek02, self.lap_of_change_Kart[0], self.Laps[-1], color='green',ls='--', linewidth=1)
                    

                elif len(self.lap_of_change_Kart) == 2:
                    plt.hlines(self.mean_sek01, 0, self.lap_of_change_Kart[0], color='lightgray',ls='--', label = f'Meantime Driver 01:  {self.mean_sek01} min')
                    plt.hlines(self.mean_sek02, self.lap_of_change_Kart[0], self.lap_of_change_Kart[1], color='lightgray',ls='--', label = f'Meantime Driver 02:  {self.mean_sek02} min')
                    plt.hlines(self.mean_sek03, self.lap_of_change_Kart[1], self.Laps[-1], color='lightgray',ls='--', label = f'Meantime Driver 03:  {self.mean_sek03} min')

                    plt.hlines(self.min_TIME_sek01, 0, self.lap_of_change_Kart[0], color='green',ls='--', linewidth=1)
                    plt.hlines(self.min_TIME_sek02, self.lap_of_change_Kart[0], self.lap_of_change_Kart[1], color='green',ls='--', linewidth=1)
                    plt.hlines(self.min_TIME_sek03, self.lap_of_change_Kart[1], self.Laps[-1], color='green',ls='--', linewidth=1)


                else:
                    print('to many Kartchanges please call Kevin Thalmann')

            #plt.text(self.fastest_lap_valid['LAP']*1.008,  self.fastest_time*0.997,   f"Time: {self.fastest_time}_absolut", verticalalignment='center', fontsize=12, color='green', bbox=props)
            plt.vlines(self.fastest_lap_valid['LAP'],0 , self.fastest_time, color='green', linewidth=1.5, label=f"Besttime abs.: {self.fastest_time} min")

        plt.title("automated evaluation by Kevin Thalmann",  fontsize=20)
        plt.xticks(self.Laps, rotation = 90)
        plt.ylim(np.min(self.ylabel)*0.99, np.max(self.ylabel)*0.99)
        plt.xlabel("Number of Laps", fontsize=15)
        plt.ylabel("Laptime", fontsize=15)
        plt.legend(loc=2, fontsize = 8)
        #plt.grid()
        plt.show()

        fig.savefig(f'03_Exported_Time.png', dpi=200)


if __name__ == '__main__':

    kartzeiten = Kartzeiten('D:\\04_TG-C23\\02_Python\\Kart\Bilder\\Kart4.jpg')
    #kartzeiten.show_picture()
    kartzeiten.kart_change_analyse()

    kartzeiten.show_laps()
    kartzeiten.show_fasted_lap()

    kartzeiten.export2csv()
    kartzeiten.plot_laps()
    
    print('#'*50)
    print(' Successful ')

"""
py -3.9 -m PyInstaller D:\04_TG-C23\02_Python\Kart\Kart.py
py -3.9 -m Pyinstaller --onefile -w 'D:\04_TG-C23\02_Python\Kart\Kart.py'
"""