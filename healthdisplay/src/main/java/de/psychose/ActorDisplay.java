package de.psychose;

import javax.swing.*;
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
    private DecimalFormat df = new DecimalFormat("#.0");

    public ActorDisplay() {
        mainPanel.setBackground(Main.backgroundColor);
    }

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

    }

    public void init(ActorData actorData) {
        this.actorData = actorData;
        lblCaption.setText(actorData.getCaption());
    }

}

