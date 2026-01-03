"""
Django management command to initialize IBOYTECH Invoice SaaS system.
Usage: python manage.py init_invoice_saas
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from invoice.models import Company, CompanyUserRole
import os


class Command(BaseCommand):
    help = 'Initialize IBOYTECH Invoice SaaS system with default company and user'

    def add_arguments(self, parser):
        parser.add_argument('--admin-email', type=str, help='Admin email address')
        parser.add_argument('--admin-password', type=str, help='Admin password')
        parser.add_argument('--company-name', type=str, default='IBOYTECH', help='Company name')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing IBOYTECH Invoice SaaS...'))

        try:
            # Check if admin user already exists
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                self.stdout.write('Creating superuser...')
                admin_email = options.get('admin_email') or 'admin@iboytech.com'
                admin_password = options.get('admin_password') or 'Admin@123456'
                
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email=admin_email,
                    password=admin_password
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Superuser created: {admin_email}'))
            else:
                self.stdout.write(f'✓ Superuser already exists: {admin_user.email}')

            # Create default company
            company_name = options.get('company_name', 'IBOYTECH')
            company, created = Company.objects.get_or_create(
                owner=admin_user,
                name=company_name,
                defaults={
                    'email': admin_user.email,
                    'phone': '+1234567890',
                    'website': 'https://iboytech.com',
                    'description': f'{company_name} - Main Company Account',
                    'country': 'NG',
                    'tax_number': 'TAX123456789',
                    'subscription_plan': 'ENTERPRISE',
                    'subscription_status': 'ACTIVE',
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Company created: {company_name}'))
            else:
                self.stdout.write(f'✓ Company already exists: {company_name}')

            # Create company user role
            role, created = CompanyUserRole.objects.get_or_create(
                user=admin_user,
                company=company,
                defaults={'role': 'OWNER'}
            )

            if created:
                self.stdout.write(self.style.SUCCESS('✓ Admin assigned as Owner'))
            else:
                self.stdout.write('✓ Admin role already assigned')

            self.stdout.write(self.style.SUCCESS('\n' + '='*50))
            self.stdout.write(self.style.SUCCESS('IBOYTECH Invoice SaaS Initialized Successfully!'))
            self.stdout.write(self.style.SUCCESS('='*50))
            self.stdout.write(f'\n📊 System Details:')
            self.stdout.write(f'   Admin User: {admin_user.username}')
            self.stdout.write(f'   Email: {admin_user.email}')
            self.stdout.write(f'   Company: {company.name}')
            self.stdout.write(f'   Plan: {company.subscription_plan}')
            self.stdout.write(f'   Status: {company.subscription_status}')
            self.stdout.write(f'\n🔐 Login Details:')
            self.stdout.write(f'   Username: admin')
            self.stdout.write(f'   Password: (your chosen password)')
            self.stdout.write(f'\n🌐 Access Points:')
            self.stdout.write(f'   Admin Panel: http://localhost:8000/admin')
            self.stdout.write(f'   Dashboard: http://localhost:8000/dashboard')
            self.stdout.write(f'\n✅ Next Steps:')
            self.stdout.write(f'   1. Start the development server: python manage.py runserver')
            self.stdout.write(f'   2. Login to admin panel')
            self.stdout.write(f'   3. Configure company settings')
            self.stdout.write(f'   4. Add team members')
            self.stdout.write(f'   5. Create invoice templates')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during initialization: {str(e)}'))
            raise
