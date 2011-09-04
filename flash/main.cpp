#include <QtGui>
#include <QAxWidget>

/**
 * 此方法仅限于Windows
 */
int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    QAxWidget *flash = new QAxWidget(0,0);
    flash->resize(1000,700);
    flash->setControl(QString::fromUtf8("{d27cdb6e-ae6d-11cf-96b8-444553540000}"));
    flash->dynamicCall("LoadMovie(long,string)",0,"E:/test/demo.swf");
    flash->show();

    return a.exec();
}
//需要在pro里加 CONFIG+=qaxcontainer
