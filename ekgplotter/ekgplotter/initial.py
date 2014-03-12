import numpy as np
import string,cgi,time, random
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn, ForkingMixIn

import re

from collections import deque

from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4 import QtGui
import pyqtgraph as pg

from pyqtgraph.widgets.PlotWidget import PlotWidget

QAPP = None

def mkQApp():
    if QtGui.QApplication.instance() is None:
        global QAPP
        QAPP = QtGui.QApplication([])


class PlotWindow(PlotWidget):
    def __init__(self, title=None, **kargs):
        mkQApp()
        self.win = QtGui.QMainWindow()
        PlotWidget.__init__(self, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        if title is not None:
            self.win.setWindowTitle(title)



plotValues = [448, 979, 301, 82, 664, 1016, 786, 752, 890, 862, 779, 566, 902, 167, 698,
            176, 356, 764, 418, 542, 1013, 179, 184, 89, 556, 806, 514, 315, 702, 297, 166,
            933, 969, 105, 444, 938, 469, 444, 413, 153, 62, 1000, 27, 195, 41, 53, 885, 541, 41, 397,
            64, 164, 117, 93, 345, 374, 327, 709, 772, 443, 483, 100, 941, 1002, 179, 269, 594, 258,
            188, 970, 360, 268, 924, 238, 633, 564, 644, 373, 279, 392, 646, 543, 295, 892, 70, 675, 675,
            173, 112, 359, 77, 831, 323, 433, 929, 790, 208, 85, 351, 266, 631, 948, 427, 991, 388, 82, 342,
            679, 492, 923, 825, 395, 357, 788, 514, 248, 153, 1002, 702, 797, 636, 200, 58, 449, 986, 979,
            461, 11, 636, 70, 874, 414, 950, 853, 561, 267, 436, 267, 349, 12, 325, 38, 322, 805, 255, 790,
            1000, 151, 621, 119, 4, 278, 699, 529, 777, 711, 791, 20, 516, 141, 728, 662, 916, 593, 362, 975,
            276, 715, 262, 988, 949, 132, 568, 618, 802, 998, 845, 238, 376, 525, 972, 1017, 985, 162, 500, 875,
            500, 944, 813, 140, 766, 750, 172, 758, 58, 140, 616, 435, 892, 811, 422, 238, 181, 638, 798,
            282, 236, 462, 308, 98, 248, 539, 925, 311, 626, 411, 113, 507, 847, 220, 439, 349, 924, 1008,
            567, 606, 402, 393, 504, 520, 910, 910, 291, 670, 598, 900, 599, 734, 637, 1009, 477, 749, 236,
            249, 9, 553, 550, 758, 801, 230, 303, 164, 412, 139, 414, 224, 348, 927, 843, 222, 98, 759, 473,
            574, 197, 988, 647, 575, 395, 715, 587, 618, 380, 599, 752, 401, 608, 875, 1002, 910, 472, 228,
            510, 734, 447, 725, 196, 31, 925, 883, 912, 797, 741, 367, 177, 16, 151, 989, 81, 574, 541, 171,
            355, 169, 56, 198, 45, 143, 694, 669, 366, 982, 1019, 350, 195, 761, 277, 1020, 202, 216, 55,
            437, 612, 144, 370, 830, 1016, 206, 1014, 306, 786, 583, 333, 366, 213, 714, 89, 907, 800,
            905, 24, 409, 163, 563, 910, 478, 328, 929, 936, 1005, 237, 705, 189, 179, 172, 958, 18, 285,
            874, 223, 667, 297, 476, 953, 124, 474, 739, 289, 656, 485, 210, 680, 110, 353, 217, 347, 8,
            1000, 607, 741, 440, 600, 170, 167, 173, 702, 105, 991, 120, 594, 567, 997, 588, 56, 480, 556,
            601, 66, 580, 625, 221, 927, 72, 710, 910, 866, 28, 440, 769, 314, 888, 615, 554, 811,
            218, 407, 763, 58, 186, 607, 212, 879, 193, 669, 371, 866, 80, 667, 730, 223, 232, 309,
            205, 329, 723, 964, 747, 718, 377, 638, 856, 440, 709, 695, 57, 72, 462, 397, 569, 811,
            999, 753, 174, 231, 638, 614, 389, 310, 789, 274, 799, 121, 762, 5, 524, 872, 401, 788,
            795, 510, 250, 740, 890, 58, 826, 352, 703, 833, 789, 373, 243, 380, 18, 753, 752, 302,
            1001, 447, 555, 666, 1023, 459, 257, 917, 29, 85, 391, 742, 575, 515, 664, 167, 336, 349,
            414, 676, 573, 165, 955, 903, 67, 863, 119, 814, 374, 181, 990, 17, 343, 549, 198, 655,
            230, 515, 671, 655, 412, 124, 963, 412, 168, 863, 149, 263, 163, 101, 889, 659, 342, 671,
            632, 342, 210, 502, 531, 1000, 661, 76, 19, 390, 569, 958, 4, 922, 979, 381, 597, 786, 138,
            110, 799, 457, 356, 648, 995, 839, 39, 241, 249, 516, 343, 166, 814, 86, 832, 125, 836, 246,
            40, 131, 907, 226, 247, 423, 390, 328, 203, 329, 209, 332, 167, 765, 506, 881, 118, 68, 15,
            593, 749, 971, 860, 268, 715, 577, 393, 999, 571, 446, 432, 488, 495, 253, 782, 371, 534, 489,
            213, 424, 136, 324, 441, 50, 669, 258, 863, 404, 1017, 132, 177, 369, 87, 763, 723, 694, 191,
            798, 98, 250, 207, 395, 586, 62, 402, 758, 9, 447, 362, 810, 57, 595, 489, 332, 559, 48, 491,
            263, 593, 6, 172, 979, 422, 798, 167, 713, 1012, 552, 8, 1, 489, 91, 613, 650, 196, 100, 402,
            429, 1023, 160, 613, 380, 756, 850, 981, 910, 66, 445, 759, 427, 699, 207, 519, 980, 789, 816,
            740, 605, 602, 816, 493, 50, 516, 738, 435, 918, 681, 626, 117, 942, 513, 686, 826, 449, 588,
            576, 116, 567, 923, 265, 646, 95, 426, 592, 67, 747, 762, 612, 286, 96, 34, 520, 1007, 817, 833,
            210, 905, 783, 866, 419, 669, 760, 215, 398, 298, 889, 867, 534, 584, 117, 34, 673, 113, 718,
            1009, 253, 554, 83, 183, 975, 463, 372, 163, 584, 446, 241, 545, 799, 316, 200, 382, 709, 311,
            340, 439, 314, 78, 603, 972, 567, 899, 88, 929, 89, 82, 387, 951, 289, 605, 337, 940, 242, 902,
            845, 494, 141, 210, 336, 636, 307, 772, 595, 500, 513, 456, 159, 823, 343, 805, 947, 12, 438,
            219, 223, 248, 675, 146, 503, 489, 1012, 644, 458, 126, 989, 505, 783, 576, 879, 367,
            442, 525, 124, 178, 831, 259, 613, 167, 71, 118, 131, 413, 355, 337, 437, 928, 636, 692, 282,
            423, 100, 191, 713, 433, 408, 794, 867, 848, 852, 551, 790, 625, 824, 998, 269, 499, 936, 483,
            687, 179, 444, 211, 999, 31, 7, 588, 232, 798, 690, 528, 288, 788, 546, 23, 594, 40, 270, 109,
            231, 484, 413, 586, 23, 81, 94, 281, 458, 494, 173, 898, 1007, 465, 516, 625, 386, 505, 348,
            348, 621, 956, 527, 293, 460, 169, 955, 136, 70, 2, 949, 997, 555, 327, 1006, 241, 13, 576,
            860, 265, 944, 26, 732, 983, 21, 135, 574, 342, 270, 687, 799, 439, 52, 84, 706, 337, 920, 717,
            764, 457, 263, 554, 651, 672, 622, 245, 739, 702, 623, 587, 332, 285, 113, 227, 659, 77, 725,
            813, 989, 925, 439, 759, 622, 545, 779, 250, 862, 511, 288, 559, 592, 819, 903, 815, 671, 226,
            83, 1007, 229, 391, 597, 608, 937, 480, 911, 208, 1004, 727, 654, 293, 107, 866, 418, 169, 333,
            462, 313, 164, 293, 22, 577, 812, 113, 926, 121, 709, 599, 434, 751, 75, 229, 399, 854, 17,
            686, 287, 212, 441, 156, 321, 888, 120, 380, 188, 696, 671, 577, 863, 1013, 294, 525, 872,
            879, 88, 30, 73, 590, 755, 647, 908, 217, 326, 804, 447, 865, 641, 730, 423, 952, 748, 867,
            482, 883, 370, 723, 7, 1020, 718, 499, 671, 21, 692, 10, 150, 359, 718, 635, 14, 111, 199,
            426, 735, 90, 797, 718, 546, 735, 160, 662, 57, 394, 834, 218, 641, 104, 542, 905, 980, 476,
            407, 436, 549, 298, 219, 10, 816, 208, 385, 504, 420, 427, 90, 328, 75, 485, 63, 389, 693, 75,
            127, 314, 318, 440, 585, 481, 91, 508, 670, 518, 890, 401, 535, 111, 725, 397, 707, 974,
            702, 323, 379, 147, 125, 248, 142, 277, 97, 370, 792, 488, 427, 324, 514, 46, 729, 41, 165,
            174, 505, 234, 744, 637, 423, 76, 558, 219, 964, 505, 663, 896, 245, 188, 347, 750, 121,
            262, 809, 905, 197, 452, 18, 901, 122, 30, 836, 908, 510, 665, 995, 774, 981, 928, 962,
            766, 459, 204, 581, 597, 739, 741, 14, 25, 169, 139, 157, 283, 299, 54, 286, 241, 184,
            320, 371, 962, 288, 261, 807, 263, 241, 969, 186, 835, 666, 97, 950, 90, 794, 111, 479,
            118, 271, 109, 247, 921, 623, 139, 450, 99, 171, 906, 604, 255, 516, 676, 888, 378, 912,
            462, 684, 974, 1002, 636, 368, 114, 237, 524, 632, 142, 963, 900, 360, 16, 987, 901,
            684, 763, 257, 528, 615, 742, 507, 230, 814, 135, 872, 253, 737, 408, 909, 491, 110,
            45, 419, 847, 788, 503, 250, 954, 271, 585, 131, 847, 880, 2, 979, 437, 513, 318,
            365, 627, 993, 558, 757, 381, 796, 119, 657, 148, 964, 495, 177, 532, 39, 69, 391, 852, 597,
            849, 283, 98, 777, 902, 749, 396, 209, 531, 142, 836, 147, 697, 189, 511, 65, 352, 867, 687,
            192, 780, 165, 413, 199, 722, 872, 326, 685, 83, 148, 353, 863, 724, 805, 549, 583, 820, 765,
            450, 224, 340, 852, 598, 128, 1014, 787, 943, 761, 790, 313, 822, 744, 18, 979, 807, 558, 964,
            679, 549, 714, 971, 767, 325, 396, 167, 70, 857, 254, 484, 640, 364, 215, 227, 244, 207, 592,
            651, 675, 307, 300, 283, 959, 286, 177, 161, 816, 790, 610, 934, 916, 998, 113, 62, 711, 663,
            71, 986, 777, 80, 56, 716, 369, 256, 524, 807, 576, 651, 292, 728, 456, 808, 1015, 26, 787,
            117, 661, 5, 298, 974, 708, 589, 113, 549, 563, 383, 1023, 531, 989, 636, 471, 820, 678, 511,
            525, 205, 255, 202, 134, 175, 799, 269, 110, 846, 27, 682, 447, 693, 122, 552, 270, 394,
            284, 606, 472, 302, 975, 796, 157, 322, 845, 955, 576, 600, 390, 82, 41, 754, 641, 87, 650,
            441, 999, 806, 349, 310, 364, 408, 30, 720, 396, 731, 959, 957, 204, 208, 1011, 644, 806, 552]

cameraQuality=75
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global cameraQuality
        global plotValues
        try:
            self.path=re.sub('[^.a-zA-Z0-9]', "",str(self.path))
            if self.path=="" or self.path==None or self.path[:1]==".":
                return
            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".mjpeg"):
                self.send_response(200)

                steps = 100
                count = 0
                plot_data1 = deque([0] * 100)
                plot_data2 = deque([0] * 100)
                plot_data3 = deque([0] * 100)
                plt = PlotWindow(title="EKG", name="Merle")
                plt.resize(1920, 1080)
                plotItem1 = pg.PlotCurveItem(pen=(0, 3*1.3))
                plotItem2 = pg.PlotCurveItem(pen=(1, 3*1.3))
                plotItem3 = pg.PlotCurveItem(pen=(2, 3*1.3))
                plotItem1.setPos(0,0*6)
                plotItem2.setPos(0,1*6)
                plotItem3.setPos(0,2*6)
                plt.addItem(plotItem1)
                plt.addItem(plotItem2)
                plt.addItem(plotItem3)

                plt.setLabel('left', "EKG")
                plt.setLabel('bottom', "Time")
                plt.showGrid(True, True)
                ba = plt.getAxis("bottom")
                bl = plt.getAxis("left")
                ba.setTicks([])
                bl.setTicks([])
                plt.setYRange(0, 1023)
                print type(plt)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")

                while 1:
                    plot_data1.appendleft(plotValues[count] / 3)
                    plot_data2.appendleft((plot_data1[0] + random.randint(-1000, 1000)) % 1023 / 3 + 1023/3)
                    plot_data3.appendleft((plot_data1[0] + random.randint(-1000, 1000)) % 1023 / 3 + 1023/3*2)
                    plot_data1.pop()
                    plot_data2.pop()
                    plot_data3.pop()
                    plotItem1.setData(np.array(plot_data1), clear=True)
                    plotItem2.setData(np.array(plot_data2), clear=True)
                    plotItem3.setData(np.array(plot_data3), clear=True)
                    exporter = pg.exporters.ImageExporter.ImageExporter(plt.plotItem)
                    #exporter.parameters()['width'] = 1920
                    name = '/tmp/tmpfs/fileName.jpg'
                    img = exporter.export(name, True)
                    buffer = QBuffer()
                    buffer.open(QIODevice.ReadWrite)
                    img.save(buffer, "JPG", 100)
                    JpegData = buffer.data()
                    self.wfile.write("--aaboundary\r\n")
                    self.wfile.write("Content-Type: image/jpeg\r\n")
                    self.wfile.write("Content-length: %d\r\n\r\n" % len(JpegData))
                    self.wfile.write(JpegData)
                    self.wfile.write("\r\n\r\n\r\n")
                    time.sleep(0.02)
                    count = (count +1) % 1500
                return
            if self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
    def do_POST(self):
        global rootnode, cameraQuality
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)

            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            value=int(upfilecontent[0])
            cameraQuality=max(2, min(99, value))
            self.wfile.write("<HTML>POST OK. Camera Set to<BR><BR>");
            self.wfile.write(str(cameraQuality));

        except :
            pass

#class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
class ThreadedHTTPServer(HTTPServer, ForkingMixIn):
    """Handle requests in a separate thread."""

def main():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', 8080), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()