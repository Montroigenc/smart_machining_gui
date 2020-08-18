import tkinter as tk
import tkinter.ttk as TTK
import cv2
import PIL.Image, PIL.ImageTk
import pyautogui
import numpy as np
import os
import glob
import ntpath
import datetime
import time
import sys

class Defect():
    def __init__(self, id, type, score):
        self.id = id
        self.type = type
        self.score = score
        self.quadrants = []

class Part():
    def __init__(self, ref, of):
        self.ref = ref
        self.of = of
        self.partStatus = 'OK'
        self.defects = []
        self.currentDefectId = -1

    def newDefect(self, type, score):
        defect = Defect(len(self.defects), type, score)
        self.defects.append(defect)
        self.currentDefectId = len(self.defects) - 1

    def removeDefect(self, id):
        del self.defects[id]
        for i, d in enumerate(self.defects):
            d.id = i

        self.currentDefectId = len(self.defects) - 1

class UserGUI():
    def __init__(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        config_path = os.path.join(application_path, "config.ini")

        self.loadConfig(config_path)
        self.inputDir = self.loadPathFromConfig(application_path, "inputDir")
        self.outputDir = self.loadPathFromConfig(application_path, "outputDir")


        self.w_partitions = int(self.configParams["widthPartitions"])
        self.h_partitions = int(self.configParams["heightPartitions"])
        self.screenSize = pyautogui.size()
        self.possibleTypes = [p for p in self.configParams["possibleTypes"].split(", ")]
        self.removeInputDirImages = self.configParams["removeInputDirImages"] == "True"
        self.imageSize = int(self.configParams["imageSize"])

        self.possibleScores = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        self.programStatus = ''

    def loadPathFromConfig(self, application_path, folderName):
        if folderName not in self.configParams:
            raise Exception('{} path not present in config file.'.format(folderName))

        path = os.path.join(application_path, self.configParams[folderName])
        if os.path.isdir(path):
            print("Input path set to {}".format(path)) if 'input' in path else print("Output path set to {}".format(path))
            return path
        else:
            raise Exception("{} directory doesn't exists.".format(path))

    def loadConfig(self, filePath):
        if os.path.isfile(filePath):
            f = open(filePath, "r", encoding='utf-8')
            data = f.read().split("\n")

            self.configParams = dict()
            for l in data:
                l = l.split(" = ")
                self.configParams["{}".format(l[0])] = l[1]

            print("{} config file loaded".format(filePath))
        else:
            raise Exception("{} config file does not exist".format(filePath))

    def userExit(self):
        sys.exit()

    def setMainWindow(self):
        self.window = 'main'
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)
        self.root.title("Contrôle estétique")

        # setting up a tkinter canvas with scrollbars
        frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])

        self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
        self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Set buttons
        self.btn_lancer = self.getButton(text="Lancer étiquetage", color="blue", fcn=lambda *args: self.changeProgramState('next'))

        # Text that displays the reference piece
        self.text_display = tk.Text(self.root, state='normal', width=40, height=15)
        self.text_display.tag_configure("right", justify='right')
        self.text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
        self.text_display.insert('end', '\nNuméro OF:\n{}\n'.format(self.currentPart.of))
        self.text_display.insert('end', '\nChemin du fichier:\n{}'.format(self.imagePath))
        self.text_display['state'] = 'disabled'

        # Place everything
        frame.grid(row=0, column=1, padx=10, pady=10, rowspan=4)  #, columnspan=3, rowspan=3)
        self.canvas.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
        self.btn_lancer.grid(row=0, column=2)
        self.text_display.grid(row=1, column=2)

        self.root.mainloop()

    def setDefectWindowLocalization(self):
        self.window = 'defectLocalization'
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)
        self.root.title("Contrôle estétique: Localisation sur la pièce")

        # setting up a tkinter canvas with scrollbars
        frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])
        self.canvas.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
        self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # mouseclick event
        self.canvas.bind("<Button 1>", self.toggleQuadrant)

        # Set buttons
        self.btn_valider = self.getButton(text="Valider localisation", color="green", fcn=lambda *args: self.changeProgramState('next'))

        # Text that displays the reference piece
        self.text_display = tk.Text(self.root, state='normal', width=20, height=8)
        self.text_display.tag_configure("right", justify='right')
        self.text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
        self.text_display.insert('end', '\nNuméro OF:\n{}'.format(self.currentPart.ref))
        self.text_display['state'] = 'disabled'

        # Text that displays the current added errors
        self.errors_display = tk.Text(self.root, state='normal', wrap='none', width=40, height=35)
        self.errors_display.insert('end', 'État pièce: {} \n'.format(self.currentPart.partStatus))
        self.errors_display.insert('end', 'Total défauts: {}\n'.format(len(self.currentPart.defects)))
        self.errors_display.insert('end', 'Défaut Type Gravité Surface\n')
        for d in self.currentPart.defects:
            self.errors_display.insert('end', '{} {} {} {}\n'.format(d.id, d.type, d.score, len(d.quadrants)))

        self.errors_display['state'] = 'disabled'

        # Place everything
        self.errors_display.grid(row=0, column=0, padx=10, pady=10, rowspan=4)
        frame.grid(row=0, column=1, padx=10, pady=10, rowspan=4)
        self.canvas.grid(row=0, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
        self.text_display.grid(row=0, column=2)
        self.btn_valider.grid(row=1, column=2)

        self.updateCanvas()

        self.root.mainloop()

    def setDefectWindow1(self):
        self.currentPart.partStatus = "OK"
        self.window = 'defect1'
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)
        self.root.title("Étape 1 – Étiquetage")

        # Text that displays the reference piece
        text_display = tk.Text(self.root, state='normal', width=20, height=8)
        text_display.tag_configure("right", justify='right')
        text_display.insert('end', 'Reference pièce:\n{}\n'.format(self.currentPart.ref))
        text_display.insert('end', '\nNuméro OF:\n{}'.format(self.currentPart.of))
        text_display['state'] = 'disabled'

        # Set buttons
        self.btn_okko = self.getButton(text="État de la    pièce: OK", color="green", fcn=self.changeBtnStatus)
        btn_next = self.getButton(text="Suivant\n->", color="blue", fcn=lambda *args: self.changeProgramState('next'))

        # Place everything
        text_display.grid(row=0, column=0, padx=10, pady=10, rowspan=2)
        self.btn_okko.grid(row=0, column=1, padx=10, pady=10)
        btn_next.grid(row=1, column=1, padx=10, pady=10)

        self.root.mainloop()

    def setDefectWindow2_0(self):
        self.window = 'defectT2_0'
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)
        self.root.title("Étape 2 – Renseignement ")

        # Set labels
        l0 = tk.Label(self.root, text="Choisissez le type et la gravité du défaut")
        l1 = tk.Label(self.root, text="Type défault:")
        l2 = tk.Label(self.root, text="Score défault:")

        # Set comboboxes
        self.comboType = TTK.Combobox(self.root, state="readonly", values=self.possibleTypes)
        self.comboScore = TTK.Combobox(self.root, state="readonly", values=self.possibleScores)

        # Set buttons
        btn_next = self.getButton(text="Localiser le defalt sur la pièce", color="blue", fcn=lambda *args: self.changeProgramState('next'))
        btn_end = self.getButton(text="Aucun défaut sur pièce", color="green", fcn=lambda *args: self.changeProgramState('end'))

        # Place everything
        l0.grid(row=0, column=0, padx=10, pady=10, columnspan=4)
        l1.grid(row=1, column=0, padx=10, pady=10, columnspan=2)
        l2.grid(row=2, column=0, padx=10, pady=10, columnspan=2)
        self.comboType.grid(row=1, column=2, padx=10, pady=10, columnspan=2)
        self.comboScore.grid(row=2, column=2, padx=10, pady=10, columnspan=2)
        btn_next.grid(row=3, column=2, padx=10, pady=10, columnspan=2)

        if self.programStatus != 'newDefect':
            btn_end.grid(row=3, column=0, padx=10, pady=10, columnspan=2)

        self.root.mainloop()

    def setDefectWindow2_1(self):
        self.window = 'defectT2_1'
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.userExit)
        self.root.title("Étape 2 – Renseignement")

        # setting up a tkinter canvas with scrollbars
        frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        self.canvas = tk.Canvas(frame, bd=0, width=self.image.shape[1], height=self.image.shape[0])
        self.canvas.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.pil_defects_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.currentPart.defects_image))
        self.image_on_canvas = self.canvas.create_image(0, 0, image=self.pil_defects_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        # Set labels
        l0 = tk.Label(self.root, text="Défaut {}/{}\nlocalisé\n".format(self.currentPart.currentDefectId + 1, len(self.currentPart.defects)), font=('Helvetica', '16'))
        l1 = tk.Label(self.root, text="Type\ndéfault", font=('Helvetica', '16'))
        l2 = tk.Label(self.root, text="Score\ndéfault", font=('Helvetica', '16'))

        # Set comboboxes
        self.comboType = TTK.Combobox(self.root, state="readonly", values=self.possibleTypes)
        self.comboType.current(self.possibleTypes.index(self.currentPart.defects[self.currentPart.currentDefectId].type))
        self.comboType.bind("<<ComboboxSelected>>", self.textBoxUpdate)

        self.comboScore = TTK.Combobox(self.root, state="readonly", values=self.possibleScores)
        self.comboScore.current(self.possibleScores.index(self.currentPart.defects[self.currentPart.currentDefectId].score))
        self.comboScore.bind("<<ComboboxSelected>>", self.textBoxUpdate)

        self.comboCurrentDefect = TTK.Combobox(self.root, state="readonly", values=["{}".format(i) for i in range(1, len(self.currentPart.defects) + 1)])
        self.comboCurrentDefect.current(self.currentPart.currentDefectId)
        self.comboCurrentDefect.bind("<<ComboboxSelected>>", self.textBoxUpdate)

        # Set buttons
        btn_modify = self.getButton(text="Modifier la localisation du défaut", color="blue", fcn=lambda *args: self.changeProgramState('next'))
        btn_delete = self.getButton(text="Supprimer cet défaut", color="red", fcn=lambda *args: self.changeProgramState('delete'))
        btn_end = self.getButton(text="Tous défauts renseignés", color="green", fcn=lambda *args: self.changeProgramState('end'))
        btn_new = self.getButton(text="Renseigner autre défault\n->", color="blue", fcn=lambda *args: self.changeProgramState('newDefect'))

        # Place everything
        l0.grid(row=0, column=0, padx=10, pady=10)
        l1.grid(row=1, column=0, padx=10, pady=10)
        l2.grid(row=2, column=0, padx=10, pady=10)
        self.comboType.grid(row=1, column=1, padx=10, pady=10)
        self.comboScore.grid(row=2, column=1, padx=10, pady=10)
        self.comboCurrentDefect.grid(row=0, column=1, padx=10, pady=10)
        btn_modify.grid(row=0, column=2, padx=10, pady=10)
        btn_delete.grid(row=1, column=2, padx=10, pady=10)
        btn_end.grid(row=3, column=0, padx=10, pady=10)
        btn_new.grid(row=3, column=2, padx=10, pady=10)
        frame.grid(row=0, column=4, padx=10, pady=10, rowspan=4)
        self.canvas.grid(row=0, column=4, sticky=tk.N + tk.S + tk.E + tk.W)

        self.updateCanvas()

        self.root.mainloop()

    def textBoxUpdate(self, event):
        self.currentPart.defects[self.currentPart.currentDefectId].type = self.comboType.get()
        self.currentPart.defects[self.currentPart.currentDefectId].score = self.comboScore.get()

        if self.currentPart.currentDefectId != int(self.comboCurrentDefect.get()) - 1:
            self.currentPart.currentDefectId = int(self.comboCurrentDefect.get()) - 1
            self.comboType.current(self.possibleTypes.index(self.currentPart.defects[self.currentPart.currentDefectId].type))
            self.comboScore.current(self.possibleScores.index(self.currentPart.defects[self.currentPart.currentDefectId].score))
            self.updateCanvas()
        
    def changeProgramState(self, s):
        self.programStatus = s
        if s == 'next':
            if 'defectT2' in self.window:
                if self.comboType.get() == "" or self.comboScore.get() == "":
                    return

                if self.window == 'defectT2_0':
                    self.currentPart.newDefect(type=self.comboType.get(), score=self.comboScore.get())

                if self.window == 'defectT2_1':
                    self.currentPart.defects[self.currentPart.currentDefectId].type = self.comboType.get()
                    self.currentPart.defects[self.currentPart.currentDefectId].score = self.comboScore.get()

        if s == 'delete':
            self.currentPart.removeDefect(self.currentPart.currentDefectId)

        self.root.destroy()
        self.root.quit()

    def changeBtnStatus(self):
        if self.btn_okko['bg'] == 'green':
            self.btn_okko.configure(bg="red", text='État de la    pièce: KO')
            self.currentPart.partStatus = "KO"
        else:
            self.btn_okko.configure(bg="green", text='État de la    pièce: OK')
            self.currentPart.partStatus = "OK"

    def getButton(self, text, color, fcn, w=12, h=3, fontSize=16):
        return tk.Button(self.root, text=text, width=w, height=h, command=fcn, bg=color, font=('Helvetica', '{}'.format(fontSize)), wraplength=160)

    def getQuadrant(self, x, y):
        yq = int(x / (self.image.shape[1] / self.w_partitions))
        xq = int(y / (self.image.shape[0] / self.h_partitions))
        return np.asarray([yq, xq])

    def plotDefectGrid(self, defect, img, screenShot=False):
        if screenShot:
            color = (0, 255, 255)
        else:
            color = (255, 255, 0) if defect.id != self.currentPart.currentDefectId else (255, 0, 0)

        vertices = np.zeros((len(defect.quadrants) * 4, 2), dtype='int')
        i = 0
        for q in defect.quadrants:
            yc, xc = self.partitions_vertices['{},{}'.format(q[0], q[1])]  # q = [col, row]
            # horizontal lines
            if not np.any(np.all(np.asarray([q[0] - 1, q[1]]) == defect.quadrants, axis=1)):
                cv2.line(img, (yc[0], xc[0]), (yc[0], xc[1]), color, 3)
            if not np.any(np.all(np.asarray([q[0] + 1, q[1]]) == defect.quadrants, axis=1)):
                cv2.line(img, (yc[1], xc[1]), (yc[1], xc[0]), color, 3)

            # vertical lines
            if not np.any(np.all(np.asarray([q[0], q[1] - 1]) == defect.quadrants, axis=1)):
                cv2.line(img, (yc[0], xc[0]), (yc[1], xc[0]), color, 3)
            if not np.any(np.all(np.asarray([q[0], q[1] + 1]) == defect.quadrants, axis=1)):
                cv2.line(img, (yc[1], xc[1]), (yc[0], xc[1]), color, 3)

            vertices[i] = [yc[0], xc[0]]
            vertices[i + 1] = [yc[1], xc[1]]
            vertices[i + 2] = [yc[0], xc[1]]
            vertices[i + 3] = [yc[1], xc[0]]
            i += 4

        maxv = vertices[np.argmax(np.sum(vertices, axis=1))]
        cv2.putText(img, "{}".format(defect.id + 1), (maxv[0] + 5, maxv[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 2, cv2.LINE_AA)

        return img

    def getUpdatedImage(self, screenShot=False):
        img = self.getGridImage()
        for defect in self.currentPart.defects:
            if len(defect.quadrants) > 0:
                img = self.plotDefectGrid(defect, img, screenShot)

        return img

    def updateCanvas(self):
        self.newImg = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.getUpdatedImage()))
        self.canvas.itemconfig(self.image_on_canvas, image=self.newImg)

    # function to be called when mouse is clicked
    def toggleQuadrant(self, event):
        q = self.getQuadrant(event.x, event.y)

        if len(self.currentPart.defects[self.currentPart.currentDefectId].quadrants) == 0:
            self.currentPart.defects[self.currentPart.currentDefectId].quadrants.append(q)
        else:
            if not np.any(np.all(q == np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants), axis=1)):
                self.currentPart.defects[self.currentPart.currentDefectId].quadrants.append(q)
            else:
                self.currentPart.defects[self.currentPart.currentDefectId].quadrants = list(np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants)[np.any(q != np.asarray(self.currentPart.defects[self.currentPart.currentDefectId].quadrants), axis=1)])

        self.updateCanvas()

    def getPartitionsVertices(self):
        w, h = self.gray.shape[1], self.gray.shape[0]
        partitions_vertices = dict()
        wp = w / self.w_partitions
        hp = h / self.h_partitions
        for y in range(self.w_partitions):
            for x in range(self.h_partitions):
                partitions_vertices['{},{}'.format(y, x)] = [[int(wp * y),  int(wp * (y + 1))], [int(hp * x),  int(hp * (x + 1))]]

        self.partitions_vertices = partitions_vertices

    def getGridImage(self):
        self.getPartitionsVertices()
        img = self.image.copy()
        wp = img.shape[1] / self.w_partitions
        hp = img.shape[0] / self.h_partitions

        for i in range(1, self.w_partitions):
            cv2.line(img, (int(wp * i), 0), (int(wp * i), img.shape[0]), (255, 255, 255), 1, 4)

        for i in range(1, self.h_partitions):
            cv2.line(img, (0, int(hp * i)), (img.shape[1], int(hp * i)), (255, 255, 255), 1, 4)

        return img

    def setFileName(self):
        # Set output file name
        dt = datetime.datetime.now().strftime('%y%m%d_%H%M')
        self.fileName = '{}/{}_{}_{}x{}_{}_{}_{}_{}'.format(self.outputDir,
                                                           self.currentPart.ref,
                                                           self.currentPart.of,
                                                           self.image.shape[0],
                                                           self.image.shape[1],
                                                           self.w_partitions,
                                                           self.h_partitions,
                                                           dt,
                                                           self.currentPart.partStatus)


    def writePartInfo(self):
        # Open file
        f = open('{}.txt'.format(self.fileName), "w+")

        # Write info
        f.write("ID TYPE SCORE QUADRANTS\n")
        for d in self.currentPart.defects:
            q = "{}".format(d.quadrants).replace(" ", "")
            l = "{} {} {} {}\n".format(d.id, d.type, d.score, q)
            l = l.replace("array(", "").replace(")", "")
            f.write(l)

        f.close()

    def createScreenShot(self):
        img = self.getUpdatedImage(screenShot=True)
        img = cv2.resize(img, (int(img.shape[1] / self.resizingRatio), int(img.shape[0] / self.resizingRatio)), interpolation=cv2.INTER_AREA)
        textBox = np.zeros((img.shape[0], 800, 3))
        x, y = 0, 50
        color = (255, 255, 255)
        text = ['Etat piece: {}'.format(self.currentPart.partStatus),
                'Total defauts: {}'.format(len(self.currentPart.defects))]

        if len(self.currentPart.defects) > 0:
            text.append('Defaut Type Gravite Surface')
            for d in self.currentPart.defects:
                text.append('{} {} {} {}'.format(d.id, d.type, d.score, len(d.quadrants)))

        for l in text:
            cv2.putText(textBox, l, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1, cv2.LINE_AA)
            y += 50

        img = np.concatenate((img, textBox), axis=1)
        cv2.imwrite('{}.png'.format(self.fileName), img)

    def __call__(self):
        while True:
            time.sleep(0.5)
            for image_path in glob.glob(os.path.join(self.inputDir, '*{}.{}'.format(self.configParams['imageToShowExtension'], self.configParams['imageExtension']))):
                self.imagePath = image_path
                fileName = ntpath.basename(image_path)
                s = fileName.split('_')
                self.currentPart = Part(ref=s[0], of=s[1])
                self.gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                self.resizingRatio = self.imageSize / max(self.gray.shape[0], self.gray.shape[1])
                self.gray = cv2.resize(self.gray, (int(self.gray.shape[1] * self.resizingRatio), int(self.gray.shape[0] * self.resizingRatio)), interpolation=cv2.INTER_AREA)
                self.image = cv2.cvtColor(self.gray, cv2.COLOR_GRAY2RGB)
                self.currentPart.defects_image = self.getGridImage()

                # State diagram
                self.setMainWindow()
                self.setDefectWindow1()
                if self.programStatus == 'next':
                    while self.programStatus != 'end':
                        if self.programStatus == 'newDefect' or len(self.currentPart.defects) == 0:
                            self.setDefectWindow2_0()
                            if self.programStatus == 'end':
                                break
                            self.programStatus = 'next'
                        if not self.programStatus == 'delete':
                            self.setDefectWindowLocalization()
                        self.setDefectWindow2_1()

                self.setFileName()
                self.writePartInfo()
                self.createScreenShot()
                if self.removeInputDirImages:
                    os.remove(image_path)

if __name__ == "__main__":
    print("Contrôle estétique app launched")
    gui = UserGUI()
    gui()