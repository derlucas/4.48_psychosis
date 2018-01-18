package de.psychose;

/**
 * @author: lucas
 * @date: 17.11.14 21:07
 */
public class ActorData {

    private String actor = "";
    private String caption = "";
    private PulseData pulseData = new PulseData();
    private int airflow;
    private int ekg;
    private int emg;
    private float temperature;
    private float temperatureOffset;
    private boolean tommyHeartbeat;

    public ActorData(String actor, String caption) {
        this.actor = actor;
        this.caption = caption;
    }

    public String getActor() {
        return actor;
    }

    public String getCaption() {
        return caption;
    }

    public int getOxygen() {
        return pulseData.getOxygen();
    }

    public void setOxygen(int oxygen) {
        pulseData.setOxygen(oxygen);
    }

    public boolean getHeartbeat() {
        return pulseData.getHeartbeat();
    }

    public void setHeartbeat(boolean heartbeat) {
        pulseData.setHeartbeat(heartbeat);
        //TODO: this is a hack due to not working EKG
/*        ekg++;
        if (ekg == 256) {
            ekg = 0;
        } */
    }

    public int getPulse() {
        return pulseData.getPulse();
    }

    public void setPulse(int pulse) {
        pulseData.setPulse(pulse);
    }

    public int getAirflow() {
        return airflow;
    }

    public void setAirflow(int airflow) {
        this.airflow = airflow;
    }

    public int getEkg() {
        return ekg;
    }

    public void setEkg(int ekg) {
        this.ekg = ekg;
    }

    public int getEmg() {
        return emg;
    }

    public void setEmg(int emg) {
        this.emg = emg;
    }

    public float getTemperature() {
        return temperature;
    }

    public void setTemperature(float temperature) {
        this.temperature = temperature;
    }

    public boolean getTommyHeartbeat() {
        return tommyHeartbeat;
    }

    public void setTommyHeartbeat(boolean tommyHeartbeat) {
        this.tommyHeartbeat = tommyHeartbeat;
    }

    public double getTemperatureOffset() {
        return temperatureOffset;
    }

    public void setTemperatureOffset(float temperatureOffset) {
        this.temperatureOffset = temperatureOffset;
    }

    @Override
    public String toString() {
        return "ActorData{" +
               "actor='" + actor + '\'' +
               ", caption='" + caption + '\'' +
               ", airflow=" + airflow +
               ", ekg=" + ekg +
               ", emg=" + emg +
               ", temperature=" + temperature +
               ", temperatureOffset=" + temperatureOffset +
               ", tommyHeartbeat=" + tommyHeartbeat +
               '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) { return true; }
        if (!(o instanceof ActorData)) { return false; }

        ActorData actorData = (ActorData) o;

        return !(actor != null ? !actor.equals(actorData.actor) : actorData.actor != null);
    }

    @Override
    public int hashCode() {
        return actor != null ? actor.hashCode() : 0;
    }
}
