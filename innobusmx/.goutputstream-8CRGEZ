import sys
from PyQt4 import QtGui


def main():
    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()



    logo = QtGui.QLabel(w)
    logo.setScaledContents(True)
    logo.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/wall2.bmp'))
    logo.move(0, 0)
    logo.resize(800, 480)

    noRed = QtGui.QLabel(w)
    noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
    noRed.setScaledContents(True)
    noRed.move(770,425)
    noRed.resize(20, 20)

    noGPS = QtGui.QLabel(w)
    noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.Jpeg"))
    noGPS.setScaledContents(True)
    noGPS.move(40,160)
    noGPS.resize(20, 20)


    w.setWindowTitle("InnobuxMX 0.1")
    w.show()
    noGPS.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
