package com.factchecker.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

/**
 * Response model for fact-checking results
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class FactCheckResponse {
    
    private String statement;
    private String verdict;
    private Double confidence;
    private String reasoning;
    
    @JsonProperty("agent_used")
    private String agentUsed;
    
    private List<Evidence> evidence;
    private String timestamp;
    
    // Error handling
    private String error;
    
    public FactCheckResponse() {}
    
    // Getters and Setters
    public String getStatement() {
        return statement;
    }
    
    public void setStatement(String statement) {
        this.statement = statement;
    }
    
    public String getVerdict() {
        return verdict;
    }
    
    public void setVerdict(String verdict) {
        this.verdict = verdict;
    }
    
    public Double getConfidence() {
        return confidence;
    }
    
    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }
    
    public String getReasoning() {
        return reasoning;
    }
    
    public void setReasoning(String reasoning) {
        this.reasoning = reasoning;
    }
    
    public String getAgentUsed() {
        return agentUsed;
    }
    
    public void setAgentUsed(String agentUsed) {
        this.agentUsed = agentUsed;
    }
    
    public List<Evidence> getEvidence() {
        return evidence;
    }
    
    public void setEvidence(List<Evidence> evidence) {
        this.evidence = evidence;
    }
    
    public String getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
    
    public String getError() {
        return error;
    }
    
    public void setError(String error) {
        this.error = error;
    }
    
    // Helper methods
    public boolean hasError() {
        return error != null && !error.trim().isEmpty();
    }
    
    public String getVerdictClass() {
        if (hasError()) return "danger";
        
        switch (verdict != null ? verdict.toUpperCase() : "") {
            case "TRUE": return "success";
            case "FALSE": return "danger";
            case "MISLEADING": return "warning";
            case "UNVERIFIED": return "secondary";
            case "NEEDS_CONTEXT": return "info";
            default: return "light";
        }
    }
    
    public String getConfidencePercentage() {
        return confidence != null ? String.format("%.1f%%", confidence * 100) : "N/A";
    }

    public ConfidenceLevel getConfidenceLevel() {
        return ConfidenceLevel.fromNumeric(confidence);
    }

    public String getConfidenceLevelDisplay() {
        return getConfidenceLevel().getDisplayName();
    }
    
    @Override
    public String toString() {
        return "FactCheckResponse{" +
                "statement='" + statement + '\'' +
                ", verdict='" + verdict + '\'' +
                ", confidence=" + confidence +
                ", reasoning='" + reasoning + '\'' +
                ", agentUsed='" + agentUsed + '\'' +
                ", error='" + error + '\'' +
                '}';
    }
    
    /**
     * Evidence model
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Evidence {
        private String source;
        private String content;
        private Double confidence;
        private Map<String, Object> metadata;
        
        public Evidence() {}
        
        // Getters and Setters
        public String getSource() {
            return source;
        }
        
        public void setSource(String source) {
            this.source = source;
        }
        
        public String getContent() {
            return content;
        }
        
        public void setContent(String content) {
            this.content = content;
        }
        
        public Double getConfidence() {
            return confidence;
        }
        
        public void setConfidence(Double confidence) {
            this.confidence = confidence;
        }
        
        public Map<String, Object> getMetadata() {
            return metadata;
        }
        
        public void setMetadata(Map<String, Object> metadata) {
            this.metadata = metadata;
        }
        
        public String getConfidencePercentage() {
            return confidence != null ? String.format("%.1f%%", confidence * 100) : "N/A";
        }

        public ConfidenceLevel getConfidenceLevel() {
            return ConfidenceLevel.fromNumeric(confidence);
        }

        public String getConfidenceLevelDisplay() {
            return getConfidenceLevel().getDisplayName();
        }
    }
}