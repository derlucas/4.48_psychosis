package de.psychose;

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
 * @date: 25.04.14 00:23
 */
public class Main {
    private ChaOSCclient chaOSCclient;
    private ControlForm controlForm;
    private MainForm mainForm;

    private int totalMessageCount = 0;
    private int messagesTempCounter = 0;

    private long totalTraffic = 0;
    private long lastTraffic = 0;

    private final ActorData actorData1 = new ActorData();
    private final ActorData actorData2 = new ActorData();
    private final ActorData actorData3 = new ActorData();


    public static void main(String[] args) {
        new Main();
    }

    public Main() {
        try {
            UIManager.setLookAndFeel("com.sun.java.swing.plaf.gtk.GTKLookAndFeel");
        } catch (Exception e) {
            e.printStackTrace();
        }

        try {
            this.chaOSCclient = new ChaOSCclient("chaosc", 7110);
            this.controlForm = new ControlForm(chaOSCclient, actorData1, actorData2, actorData3);

            final JFrame cframe = new JFrame("HD Control");
            cframe.setContentPane(controlForm.getMainPanel());
            cframe.setResizable(false);
            cframe.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
            cframe.pack();


            this.mainForm = new MainForm(actorData1, actorData2, actorData3);
            final JFrame frame = new JFrame("HD Main");
            frame.setContentPane(mainForm.getMainPanel());
            frame.setResizable(false);
            frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
//            frame.setExtendedState(JFrame.MAXIMIZED_BOTH);
            frame.setUndecorated(true);
            frame.pack();

            frame.addWindowListener(new WindowAdapter() {
                @Override
                public void windowClosing(WindowEvent e) {
                    chaOSCclient.stopReceiver();
//                    snmp.stopRunning();
                    super.windowClosing(e);
                }
            });


            addActor("merle", actorData1);
            addActor("uwe", actorData2);
            addActor("bjoern", actorData3);

            cframe.setVisible(true);
            frame.setVisible(true);

            chaOSCclient.startReceiver();

        } catch (UnknownHostException | SocketException e) {
            e.printStackTrace();
        }

    }

    private void addActor(final String actor, final ActorData actorData) {

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/heartbeat", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 3) {
                    totalMessageCount++;

                    if (message.getArguments()[1] instanceof Integer) {
                        int pulse = (int) (message.getArguments()[1]);

                        if (pulse > 60) {      // try to skip the invalid pulserate from device

                            // set the heartrate
                            actorData.getPulseData().setPulse((int) (message.getArguments()[1]));

                            // set the beat ( 0 or 1 )
                            if (message.getArguments()[0] instanceof Integer) {
                                actorData.getPulseData().setHeartbeat((int) (message.getArguments()[0]));
                            }

                            //TODO: remove this, its for testing without tommy only
                            actorData.setTommyHeartbeat(((int) message.getArguments()[0]) == 1);

                            // set the oxy level
                            if (message.getArguments()[2] instanceof Integer) {
                                actorData.getPulseData().setOxygen((int) (message.getArguments()[2]));
                            }

                            actorData.setTimestampPulse();
                        }
                    }
                }
            }
        });

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/ekg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;

                    if (message.getArguments()[0] instanceof Integer) {
                        actorData.setEkg((int) (message.getArguments()[0]));
                    }
                }
            }
        });

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/emg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;

                    if (message.getArguments()[0] instanceof Integer) {
                        actorData.setEmg((int) (message.getArguments()[0]));
                    }
                }
            }
        });

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/temperature", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;

                    if (message.getArguments()[0] instanceof Float) {
                        actorData.setTemperature((float) (message.getArguments()[0]));
                    }
                }
            }
        });

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/airFlow", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;

                    if (message.getArguments()[0] instanceof Integer) {
                        actorData.setAirflow((int) (message.getArguments()[0]));
                    }
                }
            }
        });

        chaOSCclient.addListener("/" + actor.toLowerCase() + "/tommypuls", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1) {
                    totalMessageCount++;

                    if (message.getArguments()[0] instanceof Integer) {
                        actorData.setTommyHeartbeat((boolean) (message.getArguments()[0]));
                    }
                    //TODO: evtl muss das oben hier noch anders
                }
            }
        });

    }
}
