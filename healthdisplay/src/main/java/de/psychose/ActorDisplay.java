package de.psychose;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;

/**
 * @author: lucas
 * @date: 14.04.14 21:44
 */
public class ActorDisplay {
    private final static Color onColor = Color.WHITE;
    private final static Color offColor = Color.RED;

    private JPanel actorPanel;
    private JLabel lblCaption;
    private JLabel lblHeartbeat;
    private JLabel lblPulse;
    private JLabel lblOxy;
    private JLabel lblEkg;
    private JLabel lblEmg;
    private JLabel lblTemperature;
    private JLabel lblBreath;

    private int counterHeartbeat = 0;
    private int counterPulse = 0;
    private int counterOxy = 0;
    private int counterEkg = 0;
    private int counterEmg = 0;
    private int counterTemperature = 0;
    private int counterBreath = 0;

    private int timeout = 20;   // 20 * 100ms

    public void setCaption(String caption) {
        lblCaption.setText(caption);
    }

    public void setBreath(String breath) {
        lblBreath.setText(breath);
        counterBreath = 0;
    }

    public void setTemperature(String temperature) {
        lblTemperature.setText(temperature);
        counterTemperature = 0;
    }

    public void setEkg(String value) {
        lblEkg.setText(value);
        counterEkg = 0;
    }

    public void setPulse(String pulse) {
        lblPulse.setText(pulse);
        counterPulse = 0;
    }

    public void setEmg(String emg) {
        lblEmg.setText(emg);
        counterEmg = 0;
    }

    public void setOxy(String oxy) {
        lblOxy.setText(oxy);
        counterOxy = 0;
    }

    public void setHeartbeat(String heartbeat) {
        lblHeartbeat.setText(heartbeat);
        counterHeartbeat = 0;
    }

    public ActorDisplay() {
        final Timer timer = new Timer(100, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {

                if (++counterTemperature > timeout) {
                    lblTemperature.setForeground(offColor);
                } else {
                    lblTemperature.setForeground(onColor);
                }

                if (++counterPulse > timeout) {
                    lblPulse.setForeground(offColor);
                } else {
                    lblPulse.setForeground(onColor);
                }

                if (++counterOxy > timeout) {
                    lblOxy.setForeground(offColor);
                } else {
                    lblOxy.setForeground(onColor);
                }

                if (++counterEkg > timeout) {
                    lblEkg.setForeground(offColor);
                } else {
                    lblEkg.setForeground(onColor);
                }

                if (++counterEmg > timeout) {
                    lblEmg.setForeground(offColor);
                } else {
                    lblEmg.setForeground(onColor);
                }

                if (++counterHeartbeat > timeout) {
                    lblHeartbeat.setForeground(offColor);
                    lblHeartbeat.setText("no data");
                } else {
                    lblHeartbeat.setForeground(onColor);
                }

                if (++counterBreath > timeout) {
                    lblBreath.setForeground(offColor);
                } else {
                    lblBreath.setForeground(onColor);
                }
            }
        });
        timer.setRepeats(true);
        timer.start();
    }

}

