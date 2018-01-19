package de.psychose;

import javax.swing.*;
import java.text.DecimalFormat;

/**
 * @author: lucas
 * @date: 14.04.14 21:44
 */
public class ActorDisplay {
    private JLabel lblCaption;
    private JLabel lblHeartbeat;
    private JLabel lblPulse;
    private JLabel lblOxy;
    private JLabel lblEkg;
    private JLabel lblEmg;
    private JLabel lblTemperature;
    private JLabel lblBreath;
    private JPanel mainPanel;
    private DecimalFormat df = new DecimalFormat("#.0");

    public ActorDisplay() {
        mainPanel.setBackground(Main.backgroundColor);
    }

    public void update(ActorData actorData) {
        if (actorData == null) {
            return;
        }

        lblCaption.setText(actorData.getCaption());
        lblBreath.setText(String.valueOf(actorData.getAirflow()));
        lblTemperature.setText(df.format(actorData.getTemperature()));
        lblEkg.setText(String.valueOf(actorData.getEkg()));
        lblPulse.setText(actorData.isHeartbeat() ? "systole" : "diastole");
        lblEmg.setText(String.valueOf(actorData.getEmg()));
        lblOxy.setText(String.valueOf(actorData.getOxygen()));
        lblHeartbeat.setText(String.valueOf(actorData.getPulse()));
    }
}

