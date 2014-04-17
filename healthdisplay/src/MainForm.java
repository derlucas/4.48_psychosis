import com.illposed.osc.OSCListener;
import com.illposed.osc.OSCMessage;

import javax.swing.*;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.Date;

/**
 * @author: lucas
 * @date: 14.04.14 21:43
 */
public class MainForm {
    private ChaOSCclient osCclient;

    private JPanel mainPanel;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;

    public MainForm(ChaOSCclient client) {
        osCclient = client;
        osCclient.startReceiver();

        addActor("merle", "Merle", actor1);
        addActor("uwe", "Uwe", actor2);
        addActor("bjoern", "Björn", actor3);
    }


    private void addActor(final String actor, final String label, final ActorDisplay actorDisplay) {
        actorDisplay.setCaption(label);
        osCclient.addListener("/" + actor.toLowerCase() + "/heartbeat", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 3) {
                    actorDisplay.setHeartbeat(message.getArguments()[0].toString());
                    actorDisplay.setPulse(message.getArguments()[1].toString());
                    actorDisplay.setOxy(message.getArguments()[2].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/ekg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    actorDisplay.setEkg(message.getArguments()[0].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/emg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    actorDisplay.setEmg(message.getArguments()[0].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/temperatur", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    actorDisplay.setTemperature(message.getArguments()[0].toString());
                }
            }
        });
    }

    public static void main(String[] args) {

        try {
            final ChaOSCclient chaOSCclient = new ChaOSCclient("localhost", 7110);

            final MainForm mainForm = new MainForm(chaOSCclient);
            final JFrame frame = new JFrame("MainForm");
            frame.setContentPane(mainForm.mainPanel);
            frame.setResizable(false);
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.pack();

            frame.addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    chaOSCclient.stopReceiver();
                    super.windowClosing(e);
                }
            });

            frame.setVisible(true);

            new Streamer(8888, mainForm.mainPanel).run();

        } catch (UnknownHostException e) {
            e.printStackTrace();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

}
