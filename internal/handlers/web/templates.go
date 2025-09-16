package web

import (
	"embed"
	"fmt"
	"html/template"
	"io"
	"net/http"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

//go:embed templates/*.html
var templateFS embed.FS

// Templates holds all parsed templates
type Templates struct {
	base      *template.Template
	pages     map[string]*template.Template
	fragments map[string]*template.Template
}

// NewTemplates creates and parses all templates
func NewTemplates() (*Templates, error) {
	t := &Templates{
		pages:     make(map[string]*template.Template),
		fragments: make(map[string]*template.Template),
	}

	// Parse base layout
	base, err := template.New("base").Funcs(templateFuncs()).ParseFS(templateFS, "templates/base.html")
	if err != nil {
		return nil, err
	}
	t.base = base

	// Parse page templates
	pages := []string{"login", "buildings", "dashboard"}
	for _, page := range pages {
		tmpl := template.Must(base.Clone())
		_, err = tmpl.ParseFS(templateFS, "templates/"+page+".html")
		if err != nil {
			return nil, err
		}
		t.pages[page] = tmpl
	}

	// Fragment templates would be added here when needed
	// For now, keeping it simple

	return t, nil
}

// Render renders a page template
func (t *Templates) Render(w io.Writer, page string, data interface{}) error {
	tmpl, ok := t.pages[page]
	if !ok {
		return template.Must(t.base.Clone()).Execute(w, data)
	}
	return tmpl.Execute(w, data)
}

// RenderFragment renders a fragment template for HTMX
func (t *Templates) RenderFragment(w io.Writer, fragment string, data interface{}) error {
	tmpl, ok := t.fragments[fragment]
	if !ok {
		return nil
	}
	return tmpl.Execute(w, data)
}

// templateFuncs returns custom template functions
func templateFuncs() template.FuncMap {
	return template.FuncMap{
		"formatDate": func(t time.Time) string {
			return t.Format("Jan 2, 2006")
		},
		"formatDateTime": func(t time.Time) string {
			return t.Format("Jan 2, 2006 3:04 PM")
		},
		"timeSince": func(t time.Time) string {
			duration := time.Since(t)
			if duration < time.Minute {
				return "just now"
			}
			if duration < time.Hour {
				return fmt.Sprintf("%d minutes ago", int(duration.Minutes()))
			}
			if duration < 24*time.Hour {
				return fmt.Sprintf("%d hours ago", int(duration.Hours()))
			}
			return fmt.Sprintf("%d days ago", int(duration.Hours()/24))
		},
		"statusClass": func(status string) string {
			switch status {
			case "active", "online", "healthy":
				return "text-green-600 bg-green-100"
			case "warning", "degraded":
				return "text-yellow-600 bg-yellow-100"
			case "error", "offline", "critical":
				return "text-red-600 bg-red-100"
			default:
				return "text-gray-600 bg-gray-100"
			}
		},
	}
}

// PageData represents common page data
type PageData struct {
	Title       string
	User        interface{}
	NavActive   string
	Content     interface{}
	Error       string
	Success     string
	CSRFToken   string
	CurrentTime time.Time
}

// ServeHTTP implements http.Handler for serving templates
type TemplateHandler struct {
	templates *Templates
	page      string
	dataFunc  func(*http.Request) (interface{}, error)
}

// NewTemplateHandler creates a new template handler
func NewTemplateHandler(templates *Templates, page string, dataFunc func(*http.Request) (interface{}, error)) *TemplateHandler {
	return &TemplateHandler{
		templates: templates,
		page:      page,
		dataFunc:  dataFunc,
	}
}

func (h *TemplateHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	data, err := h.dataFunc(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := h.templates.Render(w, h.page, data); err != nil {
		logger.Error("Template render error: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
	}
}
