"""
API views for report management.

This module contains ViewSets for managing reports, report templates,
and report schedules in the accounting system.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache

from accounting.models import Report, ReportTemplate, ReportSchedule
from accounting.services.report_generator import ReportGenerator
from api.serializers.reports import (
    ReportSerializer, ReportDetailSerializer, ReportSummarySerializer,
    ReportTemplateSerializer, ReportScheduleSerializer
)
from core.permissions import IsAccountantOrReadOnly, IsManagerOrReadOnly
from core.cache_utils import CacheManager


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report templates.
    
    Provides CRUD operations for report templates in the accounting system.
    """
    
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'report_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'report_type', 'sort_order', 'created_at']
    ordering = ['report_type', 'sort_order', 'name']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = ReportTemplate.objects.all()
        
        # Filter by report type if specified
        report_type = self.request.query_params.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """Get all reports generated from this template."""
        #   template = self.get_object()
        template = ReportTemplate.objects.get(id=pk)
        reports = template.reports.filter(is_deleted=False)
        
        serializer = ReportSummarySerializer(reports, many=True)
        return Response(serializer.data)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reports.
    
    Provides CRUD operations for reports in the accounting system,
    including generation, download, and status management.
    """
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAccountantOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'template', 'format', 'generated_by'
    ]
    search_fields = ['report_number', 'name', 'description']
    ordering_fields = [
        'report_number', 'name', 'status', 'created_at', 'generation_completed'
    ]
    ordering = ['-created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.report_generator = ReportGenerator()
        self.cache_manager = CacheManager('reports')
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = Report.objects.all()
        
        # Filter by template if specified
        template = self.request.query_params.get('template')
        if template:
            queryset = queryset.filter(template__name=template)
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by format if specified
        format_filter = self.request.query_params.get('format')
        if format_filter:
            queryset = queryset.filter(format=format_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return ReportDetailSerializer
        elif self.action == 'list':
            return ReportSummarySerializer
        return ReportSerializer
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate a report."""
        #  report = self.get_object()
        report = Report.objects.get(id=pk)
        
        try:
            report.start_generation(request.user)
            
            # Generate the report based on template type
            if report.template.report_type == 'BALANCE_SHEET':
                data = self.report_generator.generate_balance_sheet(
                    as_of_date=report.parameters.get('as_of_date')
                )
            elif report.template.report_type == 'INCOME_STATEMENT':
                data = self.report_generator.generate_income_statement(
                    start_date=report.parameters.get('start_date'),
                    end_date=report.parameters.get('end_date')
                )
            elif report.template.report_type == 'TRIAL_BALANCE':
                data = self.report_generator.generate_trial_balance(
                    as_of_date=report.parameters.get('as_of_date')
                )
            else:
                # For other report types, create a basic structure
                data = {
                    'report_type': report.template.report_type,
                    'generated_at': timezone.now(),
                    'parameters': report.parameters
                }
            
            # Mark report as completed
            report.complete_generation(data)
            
            # Invalidate related cache
            self.cache_manager.invalidate_report_cache()
            
            return Response({
                'message': 'Report generated successfully.',
                'report_number': report.report_number,
                'status': report.status
            })
            
        except Exception as e:
            report.fail_generation(str(e))
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a generated report."""
        #report = self.get_object()
        report = Report.objects.get(id=pk)
        
        if report.status != 'COMPLETED':
            return Response(
                {'error': 'Report is not completed yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the requested format
        requested_format = request.query_params.get('format', report.format).upper()
        
        # For now, return the report data in the requested format
        # In a real implementation, you would generate actual files
        if requested_format == 'JSON':
            return Response(report.report_data)
        elif requested_format == 'HTML':
            # Return HTML representation
            html_content = self._generate_html_report(report)
            return Response({
                'content': html_content,
                'format': 'HTML',
                'filename': f"{report.report_number}.html"
            })
        else:
            # For other formats, return the data with instructions
            return Response({
                'message': f'Report data available in {requested_format} format',
                'report_data': report.report_data,
                'format': requested_format,
                'filename': f"{report.report_number}.{requested_format.lower()}"
            })
    
    def _generate_html_report(self, report):
        """Generate a simple HTML representation of the report."""
        data = report.report_data
        
        if report.template.report_type == 'BALANCE_SHEET':
            html = f"""
            <html>
            <head><title>Balance Sheet - {report.name}</title></head>
            <body>
                <h1>Balance Sheet</h1>
                <p>As of: {data.get('as_of_date', 'N/A')}</p>
                <h2>Assets</h2>
                <ul>
            """
            for asset in data.get('assets', []):
                html += f"<li>{asset.get('name', 'N/A')}: {asset.get('balance', 0)}</li>"
            html += "</ul></body></html>"
            return html
        
        # Default HTML for other report types
        return f"""
        <html>
        <head><title>{report.name}</title></head>
        <body>
            <h1>{report.name}</h1>
            <p>Generated: {data.get('generated_at', 'N/A')}</p>
            <pre>{str(data)}</pre>
        </body>
        </html>
        """
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a report generation."""
        #report = self.get_object()
        report = Report.objects.get(id=pk)
        
        if report.status not in ['PENDING', 'GENERATING']:
            return Response(
                {'error': 'Report cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.cancel_generation()
        return Response({
            'message': 'Report generation cancelled.',
            'status': report.status
        })
    
    @action(detail=False, methods=['get'])
    def completed_reports(self, request):
        """Get all completed reports."""
        completed = self.get_queryset().filter(status='COMPLETED')
        serializer = ReportSummarySerializer(completed, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_reports(self, request):
        """Get all pending reports."""
        pending = self.get_queryset().filter(status='PENDING')
        serializer = ReportSummarySerializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failed_reports(self, request):
        """Get all failed reports."""
        failed = self.get_queryset().filter(status='FAILED')
        serializer = ReportSummarySerializer(failed, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def downloadable_reports(self, request):
        """Get all reports available for download."""
        downloadable = self.get_queryset().filter(
            status='COMPLETED',
            file_path__isnull=False
        ).exclude(file_path='')
        
        serializer = ReportSummarySerializer(downloadable, many=True)
        return Response(serializer.data)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report schedules.
    
    Provides CRUD operations for report schedules in the accounting system.
    """
    
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'frequency', 'template']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'frequency', 'next_run', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = ReportSchedule.objects.all()
        
        # Filter by frequency if specified
        frequency = self.request.query_params.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a report schedule."""
        #schedule = self.get_object()
        schedule = ReportSchedule.objects.get(id=pk)
        
        if schedule.is_active:
            return Response(
                {'error': 'Schedule is already active.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule.is_active = True
        schedule.next_run = schedule.calculate_next_run()
        schedule.save()
        
        return Response({
            'message': 'Schedule activated successfully.',
            'next_run': schedule.next_run
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a report schedule."""
        #schedule = self.get_object()
        schedule = ReportSchedule.objects.get(id=pk)
        
        if not schedule.is_active:
            return Response(
                {'error': 'Schedule is already inactive.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule.is_active = False
        schedule.next_run = None
        schedule.save()
        
        return Response({
            'message': 'Schedule deactivated successfully.'
        })
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run a scheduled report immediately."""
        #schedule = self.get_object()
        schedule = ReportSchedule.objects.get(id=pk)
        
        try:
            # Create a report from this schedule
            report = Report.objects.create(
                name=f"{schedule.name} - Manual Run",
                description=f"Manual execution of scheduled report: {schedule.name}",
                template=schedule.template,
                parameters=schedule.parameters,
                filters=schedule.filters,
                format=schedule.format,
                generated_by=request.user
            )
            
            # Generate the report
            report.start_generation(request.user)
            
            # Generate the report data
            report_generator = ReportGenerator()
            
            if schedule.template.report_type == 'BALANCE_SHEET':
                data = report_generator.generate_balance_sheet(
                    as_of_date=schedule.parameters.get('as_of_date')
                )
            elif schedule.template.report_type == 'INCOME_STATEMENT':
                data = report_generator.generate_income_statement(
                    start_date=schedule.parameters.get('start_date'),
                    end_date=schedule.parameters.get('end_date')
                )
            else:
                data = {
                    'report_type': schedule.template.report_type,
                    'generated_at': timezone.now(),
                    'parameters': schedule.parameters
                }
            
            report.complete_generation(data)
            
            return Response({
                'message': 'Report generated successfully.',
                'report_number': report.report_number,
                'report_id': str(report.id)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def active_schedules(self, request):
        """Get all active schedules."""
        active = self.get_queryset().filter(is_active=True)
        serializer = ReportScheduleSerializer(active, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_schedules(self, request):
        """Get schedules that are due to run."""
        due_schedules = []
        for schedule in self.get_queryset().filter(is_active=True):
            if schedule.should_run():
                due_schedules.append(schedule)
        
        serializer = ReportScheduleSerializer(due_schedules, many=True)
        return Response(serializer.data) 