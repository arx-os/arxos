package web

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/search"
)

// Note: Search engine and recent searches are now injected via Handler struct

// handleGlobalSearch handles the main search functionality
func (h *Handler) handleGlobalSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		// Return empty results
		h.renderSearchResults(w, []search.SearchResult{}, query)
		return
	}

	// Parse search options
	opts := search.SearchOptions{
		Query:  query,
		Limit:  20,
		Offset: 0,
	}

	// Parse filters
	if types := r.URL.Query().Get("types"); types != "" {
		opts.Types = []string{types}
	}
	if status := r.URL.Query().Get("status"); status != "" {
		opts.Status = []string{status}
	}
	if limit := r.URL.Query().Get("limit"); limit != "" {
		if l, err := strconv.Atoi(limit); err == nil {
			opts.Limit = l
		}
	}

	// Perform search
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()

	// Check if search indexer is available
	if h.searchIndexer == nil {
		logger.Error("Search indexer not initialized")
		http.Error(w, "Search functionality not available", http.StatusServiceUnavailable)
		return
	}
	
	results, err := h.searchIndexer.Search(ctx, opts)
	if err != nil {
		logger.Error("Search failed: %v", err)
		http.Error(w, "Search failed", http.StatusInternalServerError)
		return
	}

	// Track search
	if h.recentSearches != nil {
		h.recentSearches.Add(search.SearchQuery{
		Query:     query,
		Timestamp: time.Now(),
		Results:   len(results),
			UserID:    h.getUserID(r),
		})
	}

	// Check if this is an HTMX request
	if r.Header.Get("HX-Request") == "true" {
		h.renderSearchResults(w, results, query)
	} else {
		// Return JSON for API calls
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"query":   query,
			"results": results,
			"count":   len(results),
		})
	}
}

// handleSearchSuggestions provides autocomplete suggestions
func (h *Handler) handleSearchSuggestions(w http.ResponseWriter, r *http.Request) {
	prefix := r.URL.Query().Get("q")
	if len(prefix) < 2 {
		// Don't suggest for very short prefixes
		w.WriteHeader(http.StatusOK)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 500*time.Millisecond)
	defer cancel()

	// Check if search indexer is available
	if h.searchIndexer == nil {
		w.WriteHeader(http.StatusOK)
		return
	}
	
	suggestions := h.searchIndexer.Suggest(ctx, prefix, 10)

	// Return as HTML list for HTMX
	if r.Header.Get("HX-Request") == "true" {
		h.renderSuggestions(w, suggestions)
	} else {
		// Return JSON
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(suggestions)
	}
}

// handleRecentSearches returns recent search queries
func (h *Handler) handleRecentSearches(w http.ResponseWriter, r *http.Request) {
	limit := 10
	if l := r.URL.Query().Get("limit"); l != "" {
		if lim, err := strconv.Atoi(l); err == nil {
			limit = lim
		}
	}

	var recent []search.SearchQuery
	var popular []string
	
	if h.recentSearches != nil {
		recent = h.recentSearches.Get(limit)
		popular = h.recentSearches.Popular(5)
	}

	if r.Header.Get("HX-Request") == "true" {
		h.renderRecentSearches(w, recent, popular)
	} else {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"recent":  recent,
			"popular": popular,
		})
	}
}

// renderSearchResults renders search results as HTML fragments
func (h *Handler) renderSearchResults(w http.ResponseWriter, results []search.SearchResult, query string) {
	var html string

	if len(results) == 0 {
		html = fmt.Sprintf(`
		<div class="text-center py-8 text-gray-500">
			<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
			</svg>
			<p class="mt-2">No results found for "%s"</p>
			<p class="text-sm">Try adjusting your search terms</p>
		</div>`, query)
	} else {
		html = fmt.Sprintf(`<div class="space-y-4"><p class="text-sm text-gray-600 mb-2">Found %d results for "%s"</p>`, len(results), query)
		
		for _, result := range results {
			statusBadge := ""
			if result.Status != "" {
				statusColor := "gray"
				switch result.Status {
				case "normal":
					statusColor = "green"
				case "needs-repair":
					statusColor = "yellow"
				case "failed":
					statusColor = "red"
				}
				statusBadge = fmt.Sprintf(`<span class="px-2 py-1 text-xs rounded-full bg-%s-100 text-%s-800">%s</span>`,
					statusColor, statusColor, result.Status)
			}

			icon := h.getIconForType(result.Type)
			link := h.getLinkForResult(result)

			html += fmt.Sprintf(`
			<a href="%s" class="block p-4 bg-white rounded-lg border border-gray-200 hover:border-indigo-500 hover:shadow-md transition-all">
				<div class="flex items-start">
					<div class="flex-shrink-0">%s</div>
					<div class="ml-3 flex-1">
						<div class="flex items-center justify-between">
							<h4 class="text-sm font-medium text-gray-900">%s</h4>
							%s
						</div>
						<p class="text-sm text-gray-500">%s</p>
						<div class="mt-1 flex items-center text-xs text-gray-400">
							<span class="capitalize">%s</span>
							<span class="mx-2">•</span>
							<span>Score: %.1f</span>
						</div>
					</div>
				</div>
			</a>`,
				link, icon, result.Name, statusBadge, result.Description, result.Type, result.Score)
		}
		
		html += `</div>`
	}

	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, html)
}

// renderSuggestions renders autocomplete suggestions
func (h *Handler) renderSuggestions(w http.ResponseWriter, suggestions []string) {
	if len(suggestions) == 0 {
		return
	}

	html := `<div class="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto max-h-60">`
	
	for _, suggestion := range suggestions {
		html += fmt.Sprintf(`
		<div class="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-indigo-50"
		     onclick="document.getElementById('search-input').value='%s'; htmx.trigger('#search-input', 'keyup')">
			<span class="block truncate">%s</span>
		</div>`, suggestion, suggestion)
	}
	
	html += `</div>`

	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, html)
}

// renderRecentSearches renders recent and popular searches
func (h *Handler) renderRecentSearches(w http.ResponseWriter, recent []search.SearchQuery, popular []string) {
	html := `<div class="space-y-4">`
	
	// Popular searches
	if len(popular) > 0 {
		html += `<div><h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Popular Searches</h4><div class="flex flex-wrap gap-2">`
		for _, term := range popular {
			html += fmt.Sprintf(`
			<button onclick="document.getElementById('search-input').value='%s'; htmx.trigger('#search-input', 'keyup')"
			        class="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200">
				%s
			</button>`, term, term)
		}
		html += `</div></div>`
	}
	
	// Recent searches
	if len(recent) > 0 {
		html += `<div><h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Recent Searches</h4><div class="space-y-1">`
		for _, search := range recent {
			timeAgo := h.formatTimeAgo(search.Timestamp)
			html += fmt.Sprintf(`
			<div class="flex items-center justify-between py-1 hover:bg-gray-50 cursor-pointer"
			     onclick="document.getElementById('search-input').value='%s'; htmx.trigger('#search-input', 'keyup')">
				<span class="text-sm text-gray-700">%s</span>
				<span class="text-xs text-gray-400">%s • %d results</span>
			</div>`, search.Query, search.Query, timeAgo, search.Results)
		}
		html += `</div></div>`
	}
	
	html += `</div>`

	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, html)
}

// Helper methods

func (h *Handler) getIconForType(entityType string) string {
	switch entityType {
	case "building":
		return `<svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
		</svg>`
	case "equipment":
		return `<svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
		</svg>`
	case "room":
		return `<svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
		</svg>`
	default:
		return `<svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
		</svg>`
	}
}

func (h *Handler) getLinkForResult(result search.SearchResult) string {
	switch result.Type {
	case "building":
		return fmt.Sprintf("/buildings/%s/view", result.ID)
	case "equipment":
		return fmt.Sprintf("/equipment/%s", result.ID)
	case "room":
		return fmt.Sprintf("/rooms/%s", result.ID)
	default:
		return "#"
	}
}

func (h *Handler) formatTimeAgo(t time.Time) string {
	duration := time.Since(t)
	if duration < time.Minute {
		return "just now"
	} else if duration < time.Hour {
		return fmt.Sprintf("%dm ago", int(duration.Minutes()))
	} else if duration < 24*time.Hour {
		return fmt.Sprintf("%dh ago", int(duration.Hours()))
	} else {
		return fmt.Sprintf("%dd ago", int(duration.Hours()/24))
	}
}

func (h *Handler) getUserID(r *http.Request) string {
	// Get user ID from context or session
	if user := h.getUser(r); user != nil {
		// Assuming user has an ID field
		return "user-id" // Placeholder for now
	}
	return ""
}