package com.factchecker.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * Request model for fact-checking
 */
public class FactCheckRequest {
    
    @NotBlank(message = "Statement is required")
    @Size(min = 5, max = 1000, message = "Statement must be between 5 and 1000 characters")
    private String statement;
    
    private boolean useOpenAI = true;
    
    public FactCheckRequest() {}
    
    public FactCheckRequest(String statement, boolean useOpenAI) {
        this.statement = statement;
        this.useOpenAI = useOpenAI;
    }
    
    // Getters and Setters
    public String getStatement() {
        return statement;
    }
    
    public void setStatement(String statement) {
        this.statement = statement;
    }
    
    public boolean isUseOpenAI() {
        return useOpenAI;
    }
    
    public void setUseOpenAI(boolean useOpenAI) {
        this.useOpenAI = useOpenAI;
    }
    
    @Override
    public String toString() {
        return "FactCheckRequest{" +
                "statement='" + statement + '\'' +
                ", useOpenAI=" + useOpenAI +
                '}';
    }
}