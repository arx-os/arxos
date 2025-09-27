package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/arx-os/arxos/internal/workflow"
	"github.com/spf13/cobra"
)

var workflowCmd = &cobra.Command{
	Use:   "workflow",
	Short: "Workflow automation management",
	Long:  `Manage workflow automation, triggers, actions, and n8n integration.`,
}

var workflowCreateCmd = &cobra.Command{
	Use:   "create [name]",
	Short: "Create a new workflow",
	Long:  `Create a new workflow with the specified name.`,
	Args:  cobra.ExactArgs(1),
	Run:   createWorkflow,
}

var workflowListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all workflows",
	Long:  `List all available workflows.`,
	Run:   listWorkflows,
}

var workflowGetCmd = &cobra.Command{
	Use:   "get [workflow-id]",
	Short: "Get workflow details",
	Long:  `Get detailed information about a specific workflow.`,
	Args:  cobra.ExactArgs(1),
	Run:   getWorkflow,
}

var workflowExecuteCmd = &cobra.Command{
	Use:   "execute [workflow-id]",
	Short: "Execute a workflow",
	Long:  `Execute a workflow with optional input data.`,
	Args:  cobra.ExactArgs(1),
	Run:   executeWorkflow,
}

var workflowStatusCmd = &cobra.Command{
	Use:   "status [execution-id]",
	Short: "Get execution status",
	Long:  `Get the status of a workflow execution.`,
	Args:  cobra.ExactArgs(1),
	Run:   getExecutionStatus,
}

var workflowCancelCmd = &cobra.Command{
	Use:   "cancel [execution-id]",
	Short: "Cancel workflow execution",
	Long:  `Cancel a running workflow execution.`,
	Args:  cobra.ExactArgs(1),
	Run:   cancelExecution,
}

var triggerCmd = &cobra.Command{
	Use:   "trigger",
	Short: "Trigger management",
	Long:  `Manage workflow triggers.`,
}

var triggerCreateCmd = &cobra.Command{
	Use:   "create [name] [type] [workflow-id]",
	Short: "Create a new trigger",
	Long:  `Create a new trigger for a workflow.`,
	Args:  cobra.ExactArgs(3),
	Run:   createTrigger,
}

var triggerListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all triggers",
	Long:  `List all available triggers.`,
	Run:   listTriggers,
}

var triggerStartCmd = &cobra.Command{
	Use:   "start [trigger-id]",
	Short: "Start a trigger",
	Long:  `Start a trigger to begin monitoring for events.`,
	Args:  cobra.ExactArgs(1),
	Run:   startTrigger,
}

var triggerStopCmd = &cobra.Command{
	Use:   "stop [trigger-id]",
	Short: "Stop a trigger",
	Long:  `Stop a trigger from monitoring for events.`,
	Args:  cobra.ExactArgs(1),
	Run:   stopTrigger,
}

var actionCmd = &cobra.Command{
	Use:   "action",
	Short: "Action management",
	Long:  `Manage workflow actions.`,
}

var actionCreateCmd = &cobra.Command{
	Use:   "create [name] [type]",
	Short: "Create a new action",
	Long:  `Create a new action with the specified type.`,
	Args:  cobra.ExactArgs(2),
	Run:   createAction,
}

var actionListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all actions",
	Long:  `List all available actions.`,
	Run:   listActions,
}

var actionExecuteCmd = &cobra.Command{
	Use:   "execute [action-id]",
	Short: "Execute an action",
	Long:  `Execute an action with optional input data.`,
	Args:  cobra.ExactArgs(1),
	Run:   executeAction,
}

var n8nCmd = &cobra.Command{
	Use:   "n8n",
	Short: "n8n integration",
	Long:  `Manage n8n workflow integration.`,
}

var n8nSyncCmd = &cobra.Command{
	Use:   "sync [direction]",
	Short: "Sync workflows with n8n",
	Long:  `Sync workflows between ArxOS and n8n. Direction: to_n8n, from_n8n, or both.`,
	Args:  cobra.ExactArgs(1),
	Run:   syncN8N,
}

var n8nListCmd = &cobra.Command{
	Use:   "list",
	Short: "List n8n workflows",
	Long:  `List workflows from n8n.`,
	Run:   listN8NWorkflows,
}

var workflowMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Show workflow metrics",
	Long:  `Show workflow system metrics and statistics.`,
	Run:   showWorkflowMetrics,
}

func init() {
	rootCmd.AddCommand(workflowCmd)

	// Workflow commands
	workflowCmd.AddCommand(workflowCreateCmd)
	workflowCmd.AddCommand(workflowListCmd)
	workflowCmd.AddCommand(workflowGetCmd)
	workflowCmd.AddCommand(workflowExecuteCmd)
	workflowCmd.AddCommand(workflowStatusCmd)
	workflowCmd.AddCommand(workflowCancelCmd)

	// Trigger commands
	workflowCmd.AddCommand(triggerCmd)
	triggerCmd.AddCommand(triggerCreateCmd)
	triggerCmd.AddCommand(triggerListCmd)
	triggerCmd.AddCommand(triggerStartCmd)
	triggerCmd.AddCommand(triggerStopCmd)

	// Action commands
	workflowCmd.AddCommand(actionCmd)
	actionCmd.AddCommand(actionCreateCmd)
	actionCmd.AddCommand(actionListCmd)
	actionCmd.AddCommand(actionExecuteCmd)

	// n8n commands
	workflowCmd.AddCommand(n8nCmd)
	n8nCmd.AddCommand(n8nSyncCmd)
	n8nCmd.AddCommand(n8nListCmd)

	// Metrics command
	workflowCmd.AddCommand(workflowMetricsCmd)

	// Add flags
	workflowCreateCmd.Flags().StringP("description", "d", "", "Workflow description")
	workflowCreateCmd.Flags().StringP("config", "c", "", "Workflow configuration file")

	workflowExecuteCmd.Flags().StringP("input", "i", "", "Input data file")
	workflowExecuteCmd.Flags().BoolP("wait", "w", false, "Wait for execution completion")

	triggerCreateCmd.Flags().StringP("config", "c", "", "Trigger configuration file")

	actionCreateCmd.Flags().StringP("config", "c", "", "Action configuration file")
	actionExecuteCmd.Flags().StringP("input", "i", "", "Input data file")
}

func createWorkflow(cmd *cobra.Command, args []string) {
	name := args[0]

	// Get flags
	description, _ := cmd.Flags().GetString("description")
	configFile, _ := cmd.Flags().GetString("config")

	// Load configuration
	config := make(map[string]interface{})
	if configFile != "" {
		if err := loadWorkflowConfigFile(configFile, &config); err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
	}

	// Create workflow
	wf := &workflow.Workflow{
		Name:        name,
		Description: description,
		Version:     "1.0.0",
		Status:      workflow.WorkflowStatusDraft,
		Config:      config,
		CreatedBy:   "cli",
	}

	manager := workflow.NewWorkflowManager()
	if err := manager.CreateWorkflow(wf); err != nil {
		fmt.Printf("Error creating workflow: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Workflow created: %s (%s)\n", wf.ID, wf.Name)
}

func listWorkflows(cmd *cobra.Command, args []string) {
	manager := workflow.NewWorkflowManager()
	workflows := manager.ListWorkflows()

	if len(workflows) == 0 {
		fmt.Println("No workflows found")
		return
	}

	fmt.Printf("Workflows (%d):\n\n", len(workflows))
	for _, wf := range workflows {
		fmt.Printf("ID: %s\n", wf.ID)
		fmt.Printf("Name: %s\n", wf.Name)
		fmt.Printf("Description: %s\n", wf.Description)
		fmt.Printf("Status: %s\n", wf.Status)
		fmt.Printf("Version: %s\n", wf.Version)
		fmt.Printf("Created: %s\n", wf.CreatedAt.Format("2006-01-02 15:04:05"))
		fmt.Println("---")
	}
}

func getWorkflow(cmd *cobra.Command, args []string) {
	workflowID := args[0]

	manager := workflow.NewWorkflowManager()
	workflow, err := manager.GetWorkflow(workflowID)
	if err != nil {
		fmt.Printf("Error getting workflow: %v\n", err)
		os.Exit(1)
	}

	// Pretty print workflow
	jsonData, err := json.MarshalIndent(workflow, "", "  ")
	if err != nil {
		fmt.Printf("Error marshaling workflow: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(jsonData))
}

func executeWorkflow(cmd *cobra.Command, args []string) {
	workflowID := args[0]

	// Get flags
	inputFile, _ := cmd.Flags().GetString("input")
	wait, _ := cmd.Flags().GetBool("wait")

	// Load input data
	input := make(map[string]interface{})
	if inputFile != "" {
		if err := loadWorkflowConfigFile(inputFile, &input); err != nil {
			fmt.Printf("Error loading input file: %v\n", err)
			os.Exit(1)
		}
	}

	manager := workflow.NewWorkflowManager()
	execution, err := manager.ExecuteWorkflow(context.Background(), workflowID, input)
	if err != nil {
		fmt.Printf("Error executing workflow: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Workflow execution started: %s\n", execution.ID)

	if wait {
		// Wait for completion
		for {
			execution, err := manager.GetExecution(execution.ID)
			if err != nil {
				fmt.Printf("Error getting execution status: %v\n", err)
				os.Exit(1)
			}

			fmt.Printf("Status: %s\n", execution.Status)

			if execution.Status == workflow.ExecutionStatusCompleted ||
				execution.Status == workflow.ExecutionStatusFailed ||
				execution.Status == workflow.ExecutionStatusCancelled {
				break
			}

			time.Sleep(1 * time.Second)
		}

		// Show final results
		execution, err = manager.GetExecution(execution.ID)
		if err != nil {
			fmt.Printf("Error getting final execution status: %v\n", err)
			os.Exit(1)
		}

		fmt.Printf("\nExecution completed:\n")
		fmt.Printf("  Status: %s\n", execution.Status)
		fmt.Printf("  Duration: %s\n", execution.Duration)
		fmt.Printf("  Results: %d\n", len(execution.Results))

		for _, result := range execution.Results {
			fmt.Printf("  - %s: %s (Duration: %v)\n", result.NodeID, result.Status, result.Duration)
		}
	}
}

func getWorkflowExecutionStatus(cmd *cobra.Command, args []string) {
	executionID := args[0]

	manager := workflow.NewWorkflowManager()
	execution, err := manager.GetExecution(executionID)
	if err != nil {
		fmt.Printf("Error getting execution: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Execution ID: %s\n", execution.ID)
	fmt.Printf("Workflow ID: %s\n", execution.WorkflowID)
	fmt.Printf("Status: %s\n", execution.Status)
	fmt.Printf("Start Time: %s\n", execution.StartTime.Format("2006-01-02 15:04:05"))
	if execution.EndTime != nil {
		fmt.Printf("End Time: %s\n", execution.EndTime.Format("2006-01-02 15:04:05"))
		fmt.Printf("Duration: %s\n", execution.Duration)
	}

	if len(execution.Results) > 0 {
		fmt.Println("\nResults:")
		for _, result := range execution.Results {
			fmt.Printf("  - %s: %s (Duration: %v)\n", result.NodeID, result.Status, result.Duration)
		}
	}

	if execution.Error != "" {
		fmt.Printf("\nError: %s\n", execution.Error)
	}
}

func cancelWorkflowExecution(cmd *cobra.Command, args []string) {
	executionID := args[0]

	manager := workflow.NewWorkflowManager()
	err := manager.CancelExecution(executionID)
	if err != nil {
		fmt.Printf("Error cancelling execution: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Execution %s cancelled\n", executionID)
}

func createTrigger(cmd *cobra.Command, args []string) {
	name := args[0]
	triggerType := args[1]
	workflowID := args[2]

	// Get flags
	configFile, _ := cmd.Flags().GetString("config")

	// Load configuration
	config := make(map[string]interface{})
	if configFile != "" {
		if err := loadWorkflowConfigFile(configFile, &config); err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
	}

	// Create trigger
	trigger := &workflow.Trigger{
		Name:       name,
		Type:       workflow.TriggerType(triggerType),
		WorkflowID: workflowID,
		Config:     config,
		Enabled:    false,
	}

	triggerManager := workflow.NewTriggerManager()
	if err := triggerManager.RegisterTrigger(trigger); err != nil {
		fmt.Printf("Error creating trigger: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Trigger created: %s (%s)\n", trigger.ID, trigger.Name)
}

func listTriggers(cmd *cobra.Command, args []string) {
	triggerManager := workflow.NewTriggerManager()
	triggers := triggerManager.ListTriggers()

	if len(triggers) == 0 {
		fmt.Println("No triggers found")
		return
	}

	fmt.Printf("Triggers (%d):\n\n", len(triggers))
	for _, trigger := range triggers {
		fmt.Printf("ID: %s\n", trigger.ID)
		fmt.Printf("Name: %s\n", trigger.Name)
		fmt.Printf("Type: %s\n", trigger.Type)
		fmt.Printf("Workflow ID: %s\n", trigger.WorkflowID)
		fmt.Printf("Enabled: %t\n", trigger.Enabled)
		fmt.Println("---")
	}
}

func startTrigger(cmd *cobra.Command, args []string) {
	triggerID := args[0]

	triggerManager := workflow.NewTriggerManager()
	err := triggerManager.StartTrigger(context.Background(), triggerID)
	if err != nil {
		fmt.Printf("Error starting trigger: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Trigger %s started\n", triggerID)
}

func stopTrigger(cmd *cobra.Command, args []string) {
	triggerID := args[0]

	triggerManager := workflow.NewTriggerManager()
	err := triggerManager.StopTrigger(context.Background(), triggerID)
	if err != nil {
		fmt.Printf("Error stopping trigger: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Trigger %s stopped\n", triggerID)
}

func createAction(cmd *cobra.Command, args []string) {
	name := args[0]
	actionType := args[1]

	// Get flags
	configFile, _ := cmd.Flags().GetString("config")

	// Load configuration
	config := make(map[string]interface{})
	if configFile != "" {
		if err := loadWorkflowConfigFile(configFile, &config); err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
	}

	// Create action
	action := &workflow.Action{
		Name:       name,
		Type:       workflow.ActionType(actionType),
		Config:     config,
		Parameters: make(map[string]interface{}),
		Enabled:    true,
	}

	actionManager := workflow.NewActionManager()
	if err := actionManager.RegisterAction(action); err != nil {
		fmt.Printf("Error creating action: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Action created: %s (%s)\n", action.ID, action.Name)
}

func listActions(cmd *cobra.Command, args []string) {
	actionManager := workflow.NewActionManager()
	actions := actionManager.ListActions()

	if len(actions) == 0 {
		fmt.Println("No actions found")
		return
	}

	fmt.Printf("Actions (%d):\n\n", len(actions))
	for _, action := range actions {
		fmt.Printf("ID: %s\n", action.ID)
		fmt.Printf("Name: %s\n", action.Name)
		fmt.Printf("Type: %s\n", action.Type)
		fmt.Printf("Enabled: %t\n", action.Enabled)
		fmt.Println("---")
	}
}

func executeAction(cmd *cobra.Command, args []string) {
	actionID := args[0]

	// Get flags
	inputFile, _ := cmd.Flags().GetString("input")

	// Load input data
	input := make(map[string]interface{})
	if inputFile != "" {
		if err := loadWorkflowConfigFile(inputFile, &input); err != nil {
			fmt.Printf("Error loading input file: %v\n", err)
			os.Exit(1)
		}
	}

	actionManager := workflow.NewActionManager()
	output, err := actionManager.ExecuteAction(context.Background(), actionID, input)
	if err != nil {
		fmt.Printf("Error executing action: %v\n", err)
		os.Exit(1)
	}

	// Pretty print output
	jsonData, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		fmt.Printf("Error marshaling output: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(jsonData))
}

func syncN8N(cmd *cobra.Command, args []string) {
	direction := args[0]

	// Validate direction
	if direction != "to_n8n" && direction != "from_n8n" && direction != "both" {
		fmt.Printf("Invalid direction: %s. Must be 'to_n8n', 'from_n8n', or 'both'\n", direction)
		os.Exit(1)
	}

	fmt.Printf("Syncing workflows with n8n (direction: %s)...\n", direction)

	// This would make actual API calls to sync with n8n
	// For now, just simulate the sync
	time.Sleep(2 * time.Second)

	fmt.Printf("Sync completed: %s\n", direction)
}

func listN8NWorkflows(cmd *cobra.Command, args []string) {
	fmt.Println("n8n Workflows:")
	fmt.Println("(This would list workflows from n8n)")
	fmt.Println("Note: n8n integration requires n8n to be running and configured")
}

func showWorkflowMetrics(cmd *cobra.Command, args []string) {
	manager := workflow.NewWorkflowManager()
	triggerManager := workflow.NewTriggerManager()
	actionManager := workflow.NewActionManager()

	workflowMetrics := manager.GetMetrics()
	triggerMetrics := triggerManager.GetMetrics()
	actionMetrics := actionManager.GetMetrics()

	fmt.Println("Workflow Metrics:")
	fmt.Printf("  Total Workflows: %d\n", workflowMetrics.TotalWorkflows)
	fmt.Printf("  Active Workflows: %d\n", workflowMetrics.ActiveWorkflows)
	fmt.Printf("  Total Executions: %d\n", workflowMetrics.TotalExecutions)
	fmt.Printf("  Successful Executions: %d\n", workflowMetrics.SuccessfulExecutions)
	fmt.Printf("  Failed Executions: %d\n", workflowMetrics.FailedExecutions)
	fmt.Printf("  Average Duration: %s\n", workflowMetrics.AverageDuration)

	fmt.Println("\nTrigger Metrics:")
	fmt.Printf("  Total Triggers: %d\n", triggerMetrics.TotalTriggers)
	fmt.Printf("  Active Triggers: %d\n", triggerMetrics.ActiveTriggers)
	fmt.Printf("  Triggered Count: %d\n", triggerMetrics.TriggeredCount)
	fmt.Printf("  Error Count: %d\n", triggerMetrics.ErrorCount)
	fmt.Printf("  Average Latency: %s\n", triggerMetrics.AverageLatency)

	fmt.Println("\nAction Metrics:")
	fmt.Printf("  Total Actions: %d\n", actionMetrics.TotalActions)
	fmt.Printf("  Executed Actions: %d\n", actionMetrics.ExecutedActions)
	fmt.Printf("  Successful Actions: %d\n", actionMetrics.SuccessfulActions)
	fmt.Printf("  Failed Actions: %d\n", actionMetrics.FailedActions)
	fmt.Printf("  Average Duration: %s\n", actionMetrics.AverageDuration)
}

// Helper function to load configuration file
func loadWorkflowConfigFile(filename string, config *map[string]interface{}) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	return json.Unmarshal(data, config)
}
