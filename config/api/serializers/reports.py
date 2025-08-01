"""
Serializers for report-related models.

This module contains DRF serializers for Report, ReportTemplate,
and ReportSchedule models.
"""

from rest_framework import serializers
from accounting.models import Report, ReportTemplate, ReportSchedule


class ReportTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportTemplate model.
    
    Provides serialization and deserialization for report templates,
    including validation and configuration.
    """
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'report_type', 'description', 'template_config',
            'parameters', 'filters', 'is_active', 'sort_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_report_type(self, value):
        """Validate report type."""
        valid_types = [choice[0] for choice in ReportTemplate.REPORT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError("Invalid report type.")
        return value
    
    def validate_template_config(self, value):
        """Validate template configuration."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Template configuration must be a dictionary.")
        return value
    
    def validate_parameters(self, value):
        """Validate parameters list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Parameters must be a list.")
        return value
    
    def validate_filters(self, value):
        """Validate filters list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Filters must be a list.")
        return value


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Report model.
    
    Provides serialization and deserialization for reports,
    including validation and status management.
    """
    
    template = ReportTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    generation_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_number', 'name', 'description', 'template', 'template_id',
            'parameters', 'filters', 'status', 'format', 'generated_by',
            'generated_by_name', 'report_data', 'file_path', 'file_size',
            'generation_started', 'generation_completed', 'generation_time',
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'report_number', 'generated_by', 'generated_by_name',
            'report_data', 'file_path', 'file_size', 'generation_started',
            'generation_completed', 'generation_time', 'error_message',
            'created_at', 'updated_at'
        ]
    
    def validate_status(self, value):
        """Validate report status."""
        valid_statuses = [choice[0] for choice in Report.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError("Invalid report status.")
        return value
    
    def validate_format(self, value):
        """Validate report format."""
        valid_formats = [choice[0] for choice in Report.FORMAT_CHOICES]
        if value not in valid_formats:
            raise serializers.ValidationError("Invalid report format.")
        return value
    
    def validate_parameters(self, value):
        """Validate parameters dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a dictionary.")
        return value
    
    def validate_filters(self, value):
        """Validate filters dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a dictionary.")
        return value
    
    def get_generation_time(self, obj):
        """Get the time taken to generate the report."""
        return obj.get_generation_time()
    
    def to_representation(self, instance):
        """Custom representation with additional fields."""
        data = super().to_representation(instance)
        
        # Add file URL if available
        if instance.file_path:
            data['file_url'] = instance.get_file_url()
        
        # Add downloadable status
        data['is_downloadable'] = instance.is_downloadable()
        
        return data


class ReportDetailSerializer(ReportSerializer):
    """
    Detailed serializer for Report model.
    
    Includes additional fields and relationships for detailed views.
    """
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_type = serializers.CharField(source='template.report_type', read_only=True)
    
    class Meta(ReportSerializer.Meta):
        fields = ReportSerializer.Meta.fields + [
            'template_name', 'template_type'
        ]


class ReportSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for Report model.
    
    Used for lists and summaries where full details aren't needed.
    """
    
    template_name = serializers.CharField(source='template.name')
    template_type = serializers.CharField(source='template.report_type')
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_number', 'name', 'template_name', 'template_type',
            'status', 'format', 'generated_by_name', 'file_size',
            'generation_completed', 'created_at'
        ]


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportSchedule model.
    
    Provides serialization and deserialization for report schedules,
    including validation and timing information.
    """
    
    template = ReportTemplateSerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'description', 'template', 'template_id',
            'frequency', 'parameters', 'filters', 'format', 'start_date',
            'end_date', 'next_run', 'recipients', 'email_subject',
            'email_message', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_name', 'next_run',
            'created_at', 'updated_at'
        ]
    
    def validate_frequency(self, value):
        """Validate schedule frequency."""
        valid_frequencies = [choice[0] for choice in ReportSchedule.FREQUENCY_CHOICES]
        if value not in valid_frequencies:
            raise serializers.ValidationError("Invalid frequency.")
        return value
    
    def validate_format(self, value):
        """Validate report format."""
        valid_formats = [choice[0] for choice in Report.FORMAT_CHOICES]
        if value not in valid_formats:
            raise serializers.ValidationError("Invalid report format.")
        return value
    
    def validate_parameters(self, value):
        """Validate parameters dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a dictionary.")
        return value
    
    def validate_filters(self, value):
        """Validate filters dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a dictionary.")
        return value
    
    def validate_recipients(self, value):
        """Validate recipients list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Recipients must be a list.")
        
        for recipient in value:
            if not isinstance(recipient, dict):
                raise serializers.ValidationError("Each recipient must be a dictionary.")
            
            if 'email' not in recipient:
                raise serializers.ValidationError("Each recipient must have an email.")
        
        return value
    
    def validate(self, data):
        """Validate schedule data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date cannot be after end date.")
        
        return data
    
    def to_representation(self, instance):
        """Custom representation with additional fields."""
        data = super().to_representation(instance)
        
        # Add recipient information
        data['recipient_emails'] = instance.get_recipient_emails()
        data['recipient_names'] = instance.get_recipient_names()
        
        # Add should_run status
        data['should_run'] = instance.should_run()
        
        return data 