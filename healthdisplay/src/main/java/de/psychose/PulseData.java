package de.psychose;

/**
 * @author: lucas
 * @date: 03.05.14 10:58
 */
public class PulseData {

    private int heartbeat;
    private int pulse;
    private int oxygen;

    public PulseData() {

    }

    public PulseData(int heartbeat, int pulse, int oxygen) {
        this.heartbeat = heartbeat;
        this.pulse = pulse;
        this.oxygen = oxygen;
    }

    public int getHeartbeat() {
        return heartbeat;
    }

    public void setHeartbeat(int heartbeat) {
        this.heartbeat = heartbeat;
    }

    public int getPulse() {
        return pulse;
    }

    public void setPulse(int pulse) {
        this.pulse = pulse;
    }

    public int getOxygen() {
        return oxygen;
    }

    public void setOxygen(int oxygen) {
        this.oxygen = oxygen;
    }

    @Override
    public String toString() {
        return "PulseData{" +
                "heartbeat=" + heartbeat +
                ", pulse=" + pulse +
                ", oxygen=" + oxygen +
                "} ";
    }
}
