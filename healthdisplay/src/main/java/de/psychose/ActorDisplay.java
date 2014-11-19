package de.psychose;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.text.DecimalFormat;

/**
 * @author: lucas
 * @date: 14.04.14 21:44
 */
public class ActorDisplay {
    private final Timer timer;
    private final static Color onColor = Color.WHITE;
    private final static Color offColor = Color.RED;
    private final static String offText = "no data";

    private JLabel lblCaption;
    private JLabel lblHeartbeat;
    private JLabel lblPulse;
    private JLabel lblOxy;
    private JLabel lblEkg;
    private JLabel lblEmg;
    private JLabel lblTemperature;
    private JLabel lblBreath;
    private JPanel actorPanel;
    private ActorData actorData;
    private boolean showErrors = false;
    private DecimalFormat df = new DecimalFormat("#.0");

    //TODO: die einzelnen Setter wegmachen, dafür eine setData() bauen die die daten en bloc nimmt
    // die darin enthaltenen timestamps dann für rotfärbung nehmen

    public void setActorData(ActorData actorData) {
        this.actorData = actorData;
    }

    public void setCaption(String caption) {
        lblCaption.setText(caption);
    }

    public void update() {
        lblBreath.setText(String.valueOf(actorData.getAirflow()));

        lblTemperature.setText(df.format(actorData.getTemperature()));
        lblEkg.setText(String.valueOf(actorData.getEkg()));
        lblPulse.setText(actorData.getPulseData().getHeartbeat() == 0 ? "systole" : "diastole");
        lblEmg.setText(String.valueOf(actorData.getEmg()));
        lblOxy.setText(String.valueOf(actorData.getPulseData().getOxygen()));
        lblHeartbeat.setText(String.valueOf(actorData.getPulseData().getPulse()));

    }

    public ActorDisplay() {
        this.timer = new Timer(100, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {

                if (actorData == null)
                    return;

                update();

                if (showErrors) {

                    long timeout = System.currentTimeMillis() - 1000;

                    if (actorData.getTimestampTemperature() < timeout) {
                        lblTemperature.setForeground(offColor);
                        lblTemperature.setText(offText);
                    } else {
                        lblTemperature.setForeground(onColor);
                    }

                    if (actorData.getTimestampPulse() < timeout) {
                        lblPulse.setForeground(offColor);
                        lblPulse.setText(offText);
                        lblOxy.setForeground(offColor);
                        lblOxy.setText(offText);
                        lblHeartbeat.setForeground(offColor);
                        lblHeartbeat.setText(offText);
                    } else {
                        lblPulse.setForeground(onColor);
                        lblOxy.setForeground(onColor);
                        lblHeartbeat.setForeground(onColor);
                    }

                    if (actorData.getTimestampEkg() < timeout) {
                        lblEkg.setForeground(offColor);
                        lblEkg.setText(offText);
                    } else {
                        lblEkg.setForeground(onColor);
                    }

                    if (actorData.getTimestampEmg() < timeout) {
                        lblEmg.setForeground(offColor);
                        lblEmg.setText(offText);
                    } else {
                        lblEmg.setForeground(onColor);
                    }

                    if (actorData.getTimestampBreath() < timeout) {
                        lblBreath.setForeground(offColor);
                        lblBreath.setText(offText);
                    } else {
                        lblBreath.setForeground(onColor);
                    }
                }
            }
        });

        timer.setRepeats(true);
        timer.start();
    }

    public void setShowErrors(boolean showErrors) {
        this.showErrors = showErrors;
    }
}

