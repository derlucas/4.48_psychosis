package de.psychose;

import com.illposed.osc.OSCListener;
import com.illposed.osc.OSCMessage;

import javax.swing.*;
import java.awt.event.ActionEvent;
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
    private StatsDisplay statDisplay;

    private int totalMessageCount = 0;
    private int messagesTempCounter = 0;

    public MainForm(ChaOSCclient chaOSCclient) {
        osCclient = chaOSCclient;

        addActor("merle", "Proband 1", actor1);
        addActor("uwe", "Proband 2", actor2);
        addActor("bjoern", "Proband 3", actor3);

        osCclient.startReceiver();

        final Timer timer = new Timer(1000, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                statDisplay.setMessagesPerSec(String.valueOf(totalMessageCount - messagesTempCounter));
                statDisplay.setMessageCount(String.valueOf(totalMessageCount));
                messagesTempCounter = totalMessageCount;
            }
        });
        timer.setRepeats(true);
        timer.start();
    }


    private void addActor(final String actor, final String label, final ActorDisplay actorDisplay) {
        actorDisplay.setCaption(label);
        osCclient.addListener("/" + actor.toLowerCase() + "/heartbeat", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 3) {
                    totalMessageCount++;
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
                    totalMessageCount++;
                    actorDisplay.setEkg(message.getArguments()[0].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/emg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;
                    actorDisplay.setEmg(message.getArguments()[0].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/temperatur", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;
                    actorDisplay.setTemperature(message.getArguments()[0].toString());
                }
            }
        });

        osCclient.addListener("/" + actor.toLowerCase() + "/airFlow", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;
                    actorDisplay.setBreath(message.getArguments()[0].toString());
                }
            }
        });
    }

    public static void main(String[] args) {

        final String host = args.length > 0 ? args[0] : "chaosc";
        final int port = args.length > 1 ? Integer.parseInt(args[1]) : 7110;

        try {
            final ChaOSCclient chaOSCclient = new ChaOSCclient(host, port);
            final MainForm mainForm = new MainForm(chaOSCclient);
            final JFrame frame = new JFrame("MainForm");
            frame.setContentPane(mainForm.mainPanel);
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

            new Streamer(8888, mainForm.mainPanel).run();

        } catch (UnknownHostException | SocketException e) {
            e.printStackTrace();
        }
    }

}
