package de.psychose;

import javax.swing.*;
import java.awt.*;
import java.text.DecimalFormat;

/**
 * @author: lucas
 * @date: 14.04.14 21:44
 */
public class ActorDisplay {
    private static final long TIMEOUT_MILLISECONDS = 2000;
    private JLabel lblCaption;
    private JLabel lblHeartbeat;
    private JLabel lblPulse;
    private JLabel lblOxy;
    private JLabel lblEkg;
    private JLabel lblEmg;
    private JLabel lblTemperature;
    private JLabel lblBreath;
    private JPanel mainPanel;
    private ActorData actorData;
    private boolean showErrors = false;
    private DecimalFormat df = new DecimalFormat("#.0");

    public void update() {
        if (actorData == null) {
            return;
        }

        lblBreath.setText(String.valueOf(actorData.getAirflow()));
        lblTemperature.setText(df.format(actorData.getTemperature() + actorData.getTemperatureOffset()));
        lblEkg.setText(String.valueOf(actorData.getEkg()));
        lblPulse.setText(actorData.getHeartbeat() ? "systole" : "diastole");
        lblEmg.setText(String.valueOf(actorData.getEmg()));
        lblOxy.setText(String.valueOf(actorData.getOxygen()));
        lblHeartbeat.setText(String.valueOf(actorData.getPulse()));

        if (showErrors) {
            checkTimeout(lblTemperature, actorData.getTimestampTemperature());
            checkTimeout(lblPulse, actorData.getTimestampPulse());
            checkTimeout(lblOxy, actorData.getTimestampPulse());
            checkTimeout(lblHeartbeat, actorData.getTimestampPulse());
            checkTimeout(lblEkg, actorData.getTimestampEkg());
            checkTimeout(lblEmg, actorData.getTimestampEmg());
            checkTimeout(lblBreath, actorData.getTimestampBreath());
        }
    }

    public void init(ActorData actorData, final boolean showErrors) {
        this.actorData = actorData;
        lblCaption.setText(actorData.getCaption());
        this.showErrors = showErrors;
    }

    private void checkTimeout(final JLabel label, final long time) {
        if (time < System.currentTimeMillis() - TIMEOUT_MILLISECONDS) {
            label.setText("no data");
            label.setForeground(Color.red);
        } else {
            label.setForeground(Color.white);
        }
    }

}

