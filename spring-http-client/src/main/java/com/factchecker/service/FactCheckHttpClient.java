package com.factchecker.service;

import com.factchecker.model.FactCheckRequest;
import com.factchecker.model.FactCheckResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * HTTP Client for communicating with Python fact-checker server
 */
@Service
public class FactCheckHttpClient {
    
    private static final Logger logger = LoggerFactory.getLogger(FactCheckHttpClient.class);
    
    private final WebClient webClient;
    private final ObjectMapper objectMapper;
    
    @Value("${factcheck.server.url:http://localhost:8001}")
    private String factCheckServerUrl;
    
    @Value("${factcheck.server.timeout:300}")
    private int timeoutSeconds;
    
    public FactCheckHttpClient(WebClient.Builder webClientBuilder, ObjectMapper objectMapper) {
        this.webClient = webClientBuilder
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(1024 * 1024)) // 1MB
                .build();
        this.objectMapper = objectMapper;
    }
    
    /**
     * Fact-check a statement using the HTTP server
     */
    public Mono<FactCheckResponse> factCheck(FactCheckRequest request) {
        logger.info("Sending fact-check request for statement: {}", request.getStatement());
        
        try {
            // Prepare HTTP request payload
            Map<String, Object> httpRequest = Map.of(
                    "statement", request.getStatement(),
                    "use_openai", request.isUseOpenAI()
            );
            
            return webClient
                    .post()
                    .uri(factCheckServerUrl + "/fact-check")
                    .bodyValue(httpRequest)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .map(this::parseFactCheckResponse)
                    .doOnSuccess(response -> logger.info("Fact-check completed: {}", response.getVerdict()))
                    .onErrorResume(this::handleError);
                    
        } catch (Exception e) {
            logger.error("Error preparing fact-check request", e);
            return Mono.just(createErrorResponse("Failed to prepare request: " + e.getMessage()));
        }
    }
    
    /**
     * Classify a statement using the HTTP server
     */
    public Mono<Map<String, Object>> classifyStatement(String statement) {
        logger.info("Classifying statement: {}", statement);
        
        try {
            Map<String, Object> httpRequest = Map.of("statement", statement);
            
            return webClient
                    .post()
                    .uri(factCheckServerUrl + "/classify")
                    .bodyValue(httpRequest)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(timeoutSeconds / 2)) // Half timeout for classification
                    .map(this::parseJsonContent)
                    .doOnSuccess(result -> logger.info("Classification completed: {}", result.get("statement_type")))
                    .onErrorResume(error -> {
                        logger.error("Classification failed", error);
                        return Mono.just(Map.of("error", "Classification failed: " + error.getMessage()));
                    });
                    
        } catch (Exception e) {
            logger.error("Error preparing classification request", e);
            return Mono.just(Map.of("error", "Failed to prepare request: " + e.getMessage()));
        }
    }
    
    /**
     * Get server status
     */
    public Mono<Map<String, Object>> getServerStatus() {
        logger.info("Getting server status");
        
        return webClient
                .get()
                .uri(factCheckServerUrl + "/status")
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofSeconds(5))
                .map(this::parseJsonContent)
                .doOnSuccess(status -> logger.info("Server status retrieved"))
                .onErrorResume(error -> {
                    logger.error("Failed to get server status", error);
                    return Mono.just(Map.of(
                            "server", "error",
                            "message", "Failed to connect to fact-check server: " + error.getMessage()
                    ));
                });
    }
    
    // Removed MCP-specific methods - now using direct HTTP communication
    
    /**
     * Parse fact-check response from JSON content
     */
    private FactCheckResponse parseFactCheckResponse(String jsonContent) {
        try {
            return objectMapper.readValue(jsonContent, FactCheckResponse.class);
        } catch (Exception e) {
            logger.error("Failed to parse fact-check response", e);
            FactCheckResponse errorResponse = new FactCheckResponse();
            errorResponse.setError("Failed to parse response: " + e.getMessage());
            errorResponse.setVerdict("ERROR");
            errorResponse.setConfidence(0.0);
            return errorResponse;
        }
    }
    
    /**
     * Parse JSON content to Map
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> parseJsonContent(String jsonContent) {
        try {
            return objectMapper.readValue(jsonContent, Map.class);
        } catch (Exception e) {
            logger.error("Failed to parse JSON content", e);
            return Map.of("error", "Failed to parse response: " + e.getMessage());
        }
    }
    
    /**
     * Handle errors and create error responses
     */
    private Mono<FactCheckResponse> handleError(Throwable error) {
        logger.error("HTTP client error", error);
        
        String errorMessage;
        if (error instanceof WebClientException) {
            errorMessage = "Failed to connect to fact-checker server. Please ensure the Python HTTP server is running.";
        } else {
            errorMessage = "Fact-checking failed: " + error.getMessage();
        }
        
        return Mono.just(createErrorResponse(errorMessage));
    }
    
    /**
     * Create error response
     */
    private FactCheckResponse createErrorResponse(String errorMessage) {
        FactCheckResponse errorResponse = new FactCheckResponse();
        errorResponse.setError(errorMessage);
        errorResponse.setVerdict("ERROR");
        errorResponse.setConfidence(0.0);
        errorResponse.setReasoning("System error occurred during fact-checking");
        return errorResponse;
    }
}