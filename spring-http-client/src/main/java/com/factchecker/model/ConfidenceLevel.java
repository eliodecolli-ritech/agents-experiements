package com.factchecker.model;

/**
 * Enumeration for confidence levels in fact-checking results
 */
public enum ConfidenceLevel {
    VERY_LOW("Very Low", 0.0, 0.2),
    LOW("Low", 0.2, 0.4),
    MEDIUM("Medium", 0.4, 0.6),
    HIGH("High", 0.6, 0.8),
    VERY_HIGH("Very High", 0.8, 1.0);

    private final String displayName;
    private final double minValue;
    private final double maxValue;

    ConfidenceLevel(String displayName, double minValue, double maxValue) {
        this.displayName = displayName;
        this.minValue = minValue;
        this.maxValue = maxValue;
    }

    public String getDisplayName() {
        return displayName;
    }

    public double getMinValue() {
        return minValue;
    }

    public double getMaxValue() {
        return maxValue;
    }

    /**
     * Convert numeric confidence (0.0-1.0) to confidence level
     */
    public static ConfidenceLevel fromNumeric(Double confidence) {
        if (confidence == null) {
            return VERY_LOW;
        }

        if (confidence >= VERY_HIGH.minValue) return VERY_HIGH;
        if (confidence >= HIGH.minValue) return HIGH;
        if (confidence >= MEDIUM.minValue) return MEDIUM;
        if (confidence >= LOW.minValue) return LOW;
        return VERY_LOW;
    }

    /**
     * Get representative numeric value (midpoint of range)
     */
    public double getRepresentativeValue() {
        return (minValue + maxValue) / 2.0;
    }

    /**
     * Get CSS class for styling
     */
    public String getCssClass() {
        switch (this) {
            case VERY_HIGH: return "confidence-very-high";
            case HIGH: return "confidence-high";
            case MEDIUM: return "confidence-medium";
            case LOW: return "confidence-low";
            case VERY_LOW: return "confidence-very-low";
            default: return "confidence-unknown";
        }
    }

    /**
     * Get Bootstrap color class
     */
    public String getBootstrapClass() {
        switch (this) {
            case VERY_HIGH: return "success";
            case HIGH: return "primary";
            case MEDIUM: return "warning";
            case LOW: return "secondary";
            case VERY_LOW: return "danger";
            default: return "light";
        }
    }
}