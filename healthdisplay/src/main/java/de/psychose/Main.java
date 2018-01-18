package de.psychose;

import com.illposed.osc.OSCListener;
import com.illposed.osc.OSCMessage;

import javax.swing.*;
import java.awt.*;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.Date;

/**
 * @author: lucas
 * @date: 25.04.14 00:23
 */
public class Main {

    public static Color backgroundColor = Color.black;
    private MainForm mainForm;
    private ControlForm controlForm;

    public static void main(String[] args) {
        new Main();
    }

    public Main() {
        final ActorData[] actorDatas = new ActorData[3];
        actorDatas[0] = new ActorData("merle", "Körper 1");
        actorDatas[1] = new ActorData("uwe", "Körper 2");
        actorDatas[2] = new ActorData("bjoern", "Körper 3");

        try {
            UIManager.setLookAndFeel("com.sun.java.swing.plaf.gtk.GTKLookAndFeel");
        }
        catch (Exception e) {
            e.printStackTrace();
        }

        try {
            final ChaOSCclient chaOSCclient = new ChaOSCclient("chaosc.lan", 7110);

            for (ActorData actorData : actorDatas) {
                addActorOSCListeners(chaOSCclient, actorData);
            }

            chaOSCclient.startReceiver();

            controlForm = new ControlForm(chaOSCclient, actorDatas);
            mainForm = new MainForm(actorDatas);

            Runtime.getRuntime().addShutdownHook(new Thread(
                new Runnable() {
                    @Override
                    public void run() {
                        chaOSCclient.stopReceiver();
                    }
                }
            ));
        }
        catch (UnknownHostException | SocketException e) {
            e.printStackTrace();
        }
    }

    private void addActorOSCListeners(final ChaOSCclient chaOSCclient, final ActorData actorData) {

        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/heartbeat", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 3) {

                    // set the beat ( 0 or 1 )
                    if (message.getArguments()[0] instanceof Integer) {
                        actorData.setHeartbeat((int) (message.getArguments()[0]) == 1);
                    }

                    // set the heartrate
                    if (message.getArguments()[1] instanceof Integer) {
                        final int pulse = (int) (message.getArguments()[1]);
                        if (pulse > 60) {      // try to skip the invalid pulse rate from device
                            actorData.setPulse(pulse);
                        }
                    }

                    // set the oxy level
                    if (message.getArguments()[2] instanceof Integer) {
                        actorData.setOxygen((int) (message.getArguments()[2]));
                    }

                    Main.this.update();
                }
            }
        });

        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/ekg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1 && message.getArguments()[0] instanceof Integer) {
                    actorData.setEkg((int) (message.getArguments()[0]));
                    Main.this.update();
                }
            }
        });

        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/emg", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1 && message.getArguments()[0] instanceof Integer) {
                    actorData.setEmg((int) (message.getArguments()[0]));
                    Main.this.update();
                }
            }
        });

        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/temperature", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1 && message.getArguments()[0] instanceof Float) {
                    actorData.setTemperature((float) (message.getArguments()[0]));
                    Main.this.update();
                }
            }
        });

        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/airFlow", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 1 && message.getArguments()[0] instanceof Integer) {
                    actorData.setAirflow((int) (message.getArguments()[0]));
                    Main.this.update();
                }
            }
        });

        //TODO: evtl muss das oben hier noch anders
        chaOSCclient.addListener("/" + actorData.getActor().toLowerCase() + "/tommyheartbeat",
                                 new OSCListener() {
                                     @Override
                                     public void acceptMessage(Date time, OSCMessage message) {
                                         actorData.setTommyHeartbeat(!actorData.getTommyHeartbeat());
                                         Main.this.update();
                                     }
                                 });
    }

    private void update() {
        //mainForm.update();
    }
}
