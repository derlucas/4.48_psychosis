package de.psychose;

import javax.swing.*;
import java.awt.event.ActionEvent;
import java.text.DecimalFormat;

/**
 * @author: lucas
 * @date: 14.04.14 21:43
 */
public class MainForm {
    private JPanel mainPanel;
    private ActorHeart heart1;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;
    private JLabel breath;
    private final DecimalFormat df = new DecimalFormat("#.0");

    public JPanel getMainPanel() {
        return mainPanel;
    }

    public MainForm(final ActorData actorData1, final ActorData actorData2, final ActorData actorData3) {

        actor1.setCaption("Körper 1");
        actor2.setCaption("Körper 2");
        actor3.setCaption("Körper 3");
        actor1.setActorData(actorData1);
        actor2.setActorData(actorData2);
        actor3.setActorData(actorData3);
        heart1.setActorData(actorData1, actorData2, actorData3);

        final Timer timer = new Timer(100, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                breath.setText(String.valueOf(actorData1.getAirflow()));
            }
        });
        timer.setRepeats(true);
        timer.start();

    }





}
