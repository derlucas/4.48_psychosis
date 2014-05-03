package de.psychose;

import com.illposed.osc.OSCListener;
import com.illposed.osc.OSCMessage;

import javax.swing.*;
import java.awt.event.ActionEvent;
import java.util.Date;
import java.util.Observable;
import java.util.Observer;

/**
 * @author: lucas
 * @date: 14.04.14 21:43
 */
public class MainForm {
    private final ChaOSCclient osCclient;
    private JPanel mainPanel;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;
    private StatsDisplay statDisplay;
    private PulseControl pulse1;
    private PulseControl pulse2;
    private PulseControl pulse3;

    private int totalMessageCount = 0;
    private int messagesTempCounter = 0;

    private long totalTraffic = 0;
    private long lastTraffic = 0;

    public JPanel getMainPanel() {
        return mainPanel;
    }

    public MainForm(final boolean showErrors, final ChaOSCclient chaOSCclient, final SnmpStatClient snmpStatClient) {
        this.osCclient = chaOSCclient;

        addActor("merle", "Körper 1", actor1, pulse1);
        addActor("uwe", "Körper 2", actor2, pulse2);
        addActor("bjoern", "Körper 3", actor3, pulse3);


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

        final Timer snmpTimer = new Timer(5000, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                totalTraffic = snmpStatClient.getTrafficSum();  // in kB
                statDisplay.setTotalTraffic(String.valueOf(totalTraffic));
                statDisplay.setBandwidth(String.valueOf((totalTraffic - lastTraffic) / 5));
                lastTraffic = totalTraffic;
            }
        });
        snmpTimer.setRepeats(true);


        if(showErrors) {
            actor1.startErrorTimer();
            actor2.startErrorTimer();
            actor3.startErrorTimer();
            snmpTimer.start();
        } else {
            pulse1.hide();
            pulse2.hide();
            pulse3.hide();
            statDisplay.hide();
        }
    }


    private void addActor(final String actor, final String label, final ActorDisplay actorDisplay, final PulseControl pulse) {
        actorDisplay.setCaption(label);
        osCclient.addListener("/" + actor.toLowerCase() + "/heartbeat", new OSCListener() {
            @Override
            public void acceptMessage(Date time, OSCMessage message) {
                if (message.getArguments().length == 3) {
                    totalMessageCount++;
                    actorDisplay.setHeartbeat(message.getArguments()[0].toString().equals("0") ? "Systole" : "Diastole");
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

        pulse.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if(arg instanceof PulseData) {
                    final PulseData data = (PulseData)arg;
                    osCclient.sendPulse(actor, data.getHeartbeat(), data.getPulse(), data.getOxygen());
                }
            }
        });
    }



}
