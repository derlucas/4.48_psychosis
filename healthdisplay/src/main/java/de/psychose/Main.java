package de.psychose;

import javax.swing.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.net.SocketException;
import java.net.UnknownHostException;

/**
 * @author: lucas
 * @date: 25.04.14 00:23
 */
public class Main {


    public static void main(String[] args) {

        final boolean showErrors = args.length > 0;

        try
        {
            //UIManager.setLookAndFeel( UIManager.getSystemLookAndFeelClassName() );
            UIManager.setLookAndFeel( "com.sun.java.swing.plaf.gtk.GTKLookAndFeel" );
        }
        catch ( Exception e )
        {
            e.printStackTrace();
        }

        try {
            final ChaOSCclient chaOSCclient = new ChaOSCclient("chaosc", 7110);
            final SnmpStatClient snmp = new SnmpStatClient("switch/161");
            final MainForm mainForm = new MainForm(showErrors, chaOSCclient, snmp);
            final JFrame frame = new JFrame("MainForm");
            frame.setContentPane(mainForm.getMainPanel());
            frame.setResizable(false);
            frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
            frame.pack();

            frame.addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    chaOSCclient.stopReceiver();
                    super.windowClosing(e);
                }
            });

            frame.setVisible(true);

            new Streamer(8888, mainForm.getMainPanel()).run();

            chaOSCclient.startReceiver();

        } catch (UnknownHostException | SocketException e) {
            e.printStackTrace();
        }
    }

}
