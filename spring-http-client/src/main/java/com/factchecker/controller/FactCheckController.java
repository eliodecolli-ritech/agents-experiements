package com.factchecker.controller;

import com.factchecker.model.FactCheckRequest;
import com.factchecker.model.FactCheckResponse;
import com.factchecker.service.FactCheckHttpClient;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * Main controller for the fact-checking web interface
 */
@Controller
public class FactCheckController {
    
    private static final Logger logger = LoggerFactory.getLogger(FactCheckController.class);
    
    @Autowired
    private FactCheckHttpClient httpClient;
    
    /**
     * Home page - displays the fact-checking form
     */
    @GetMapping("/")
    public String home(Model model) {
        logger.info("Displaying home page");
        
        // Add empty form object
        model.addAttribute("factCheckRequest", new FactCheckRequest());
        
        // Get server status asynchronously
        httpClient.getServerStatus()
                .subscribe(
                        status -> model.addAttribute("serverStatus", status),
                        error -> {
                            logger.warn("Could not retrieve server status: {}", error.getMessage());
                            model.addAttribute("serverStatus", Map.of(
                                    "server", "unknown",
                                    "message", "Status unavailable"
                            ));
                        }
                );
        
        return "index";
    }
    
    /**
     * Process fact-check request
     */
    @PostMapping("/fact-check")
    public String factCheck(@Valid @ModelAttribute FactCheckRequest factCheckRequest,
                          BindingResult bindingResult,
                          Model model,
                          RedirectAttributes redirectAttributes) {
        
        logger.info("Processing fact-check request: {}", factCheckRequest.getStatement());
        
        // Handle validation errors
        if (bindingResult.hasErrors()) {
            logger.warn("Validation errors in fact-check request");
            model.addAttribute("factCheckRequest", factCheckRequest);
            return "index";
        }
        
        try {
            // Perform fact-checking via HTTP client
            FactCheckResponse response = httpClient.factCheck(factCheckRequest).block();
            
            if (response != null) {
                model.addAttribute("factCheckResponse", response);
                model.addAttribute("factCheckRequest", factCheckRequest);
                
                logger.info("Fact-check completed - Verdict: {}, Confidence: {}", 
                          response.getVerdict(), response.getConfidencePercentage());
            } else {
                model.addAttribute("error", "No response received from fact-checker server");
                model.addAttribute("factCheckRequest", factCheckRequest);
                logger.error("Received null response from HTTP client");
            }
            
        } catch (Exception e) {
            logger.error("Error during fact-checking", e);
            model.addAttribute("error", "Error occurred during fact-checking: " + e.getMessage());
            model.addAttribute("factCheckRequest", factCheckRequest);
        }
        
        return "index";
    }
    
    /**
     * AJAX endpoint for real-time statement classification
     */
    @PostMapping("/classify")
    @ResponseBody
    public Mono<Map<String, Object>> classifyStatement(@RequestBody Map<String, String> request) {
        String statement = request.get("statement");
        
        if (statement == null || statement.trim().isEmpty()) {
            return Mono.just(Map.of("error", "Statement is required"));
        }
        
        logger.info("Classifying statement via AJAX: {}", statement);
        
        return httpClient.classifyStatement(statement.trim())
                .doOnSuccess(result -> logger.debug("Classification result: {}", result))
                .doOnError(error -> logger.error("Classification error", error));
    }
    
    /**
     * Status endpoint - returns server and system status
     */
    @GetMapping("/status")
    @ResponseBody
    public Mono<Map<String, Object>> getStatus() {
        logger.info("Status endpoint requested");
        
        return httpClient.getServerStatus()
                .map(status -> {
                    // Add client-side information
                    status.put("client_version", "1.0.0");
                    status.put("client_status", "running");
                    return status;
                })
                .doOnSuccess(status -> logger.debug("Status response: {}", status));
    }
    
    /**
     * About page
     */
    @GetMapping("/about")
    public String about(Model model) {
        logger.info("Displaying about page");
        
        model.addAttribute("systemInfo", Map.of(
                "name", "Fact-Checker System",
                "version", "1.0.0",
                "description", "Hybrid fact-checking using RAG (company data) and Wikipedia agents",
                "architecture", "Spring AI HTTP Client → Python HTTP Server → LangGraph Orchestrator",
                "agents", new String[]{"RAG Agent (MongoDB + Qdrant)", "Wikipedia Agent", "LangGraph Orchestrator"}
        ));
        
        return "about";
    }
    
    /**
     * Error handler for general exceptions
     */
    @ExceptionHandler(Exception.class)
    public String handleException(Exception e, Model model) {
        logger.error("Unhandled exception in controller", e);
        
        model.addAttribute("error", "An unexpected error occurred: " + e.getMessage());
        model.addAttribute("factCheckRequest", new FactCheckRequest());
        
        return "index";
    }
}