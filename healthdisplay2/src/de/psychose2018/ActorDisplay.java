package de.psychose2018;

import processing.core.PApplet;
import processing.core.PFont;
import processing.core.PImage;

public class ActorDisplay {

    private final PApplet host;
    private final PImage heart1;
    private final PImage heart2;
    private final ActorData actorData;
    private final PFont titleFont;
    private final PFont mainFont;

    ActorDisplay(PApplet host, PFont titleFont, PFont mainFont, PImage heart1, PImage heart2, ActorData data) {
        this.host = host;
        this.actorData = data;
        this.heart1 = heart1;
        this.heart2 = heart2;
        this.titleFont = titleFont;
        this.mainFont = mainFont;
    }


    void display() {

        host.textFont(titleFont);
        host.textAlign(host.LEFT, host.BOTTOM);
        host.text(actorData.getCaption(), 40, -10);

        host.textFont(mainFont);
        host.textAlign(host.LEFT, host.TOP);

        int i = 0;
        int textSpacing = 29;
        int startX = 25;
        host.text("Herz", startX, i++ * textSpacing);
        host.text("Puls", startX, i++ * textSpacing);
        host.text("Oxy", startX, i++ * textSpacing);
        host.text("EKG", startX, i++ * textSpacing);
        host.text("EMG", startX, i++ * textSpacing);
        host.text("Temp", startX, i++ * textSpacing);
        host.text("Atem", startX, i++ * textSpacing);


        host.textAlign(host.RIGHT, host.TOP);
        i = 0;
        host.text(actorData.getPulse(), 205, i++ * textSpacing);
        host.text(actorData.isHeartbeat() ? "systole" : "diastole", 205, i++ * textSpacing);
        host.text(actorData.getOxygen(), 205, i++ * textSpacing);
        host.text(actorData.getEkg(), 205, i++ * textSpacing);
        host.text(actorData.getEmg(), 205, i++ * textSpacing);
        host.text(String.format("%2.1f", actorData.getTemperature()), 205, i++ * textSpacing);
        host.text(actorData.getAirflow(), 205, i++ * textSpacing);


        host.image(actorData.isHeartbeat() ? heart1 : heart2, 0, 220);

    }
}
