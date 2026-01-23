# Generated migration for adding district field and renaming state to province

from django.db import migrations, models
import apps.branch.models


def migrate_state_to_province(apps, schema_editor):
    """
    Migrate existing state values to province.
    If state has a value and it's in NEPAL_PROVINCE_DISTRICTS, use it as province.
    Otherwise, set it to the first province with a default district.
    """
    Branch = apps.get_model('branch', 'Branch')
    NEPAL_PROVINCE_DISTRICTS = {
        'Koshi': ['Bhojpur', 'Dhankuta', 'Ilam', 'Jhapa', 'Khotang', 'Morang', 'Okhaldhunga', 'Panchthar', 'Sankhuwasabha', 'Solukhumbu', 'Sunsari', 'Taplejung', 'Terhathum', 'Udayapur'],
        'Madhesh': ['Bara', 'Dhanusha', 'Mahottari', 'Parsa', 'Rautahat', 'Saptari', 'Sarlahi', 'Siraha'],
        'Bagmati': ['Bhaktapur', 'Chitwan', 'Dhading', 'Dolakha', 'Kathmandu', 'Kavrepalanchok', 'Lalitpur', 'Makwanpur', 'Nuwakot', 'Ramechhap', 'Rasuwa', 'Sindhuli', 'Sindhupalchok'],
        'Gandaki': ['Baglung', 'Gorkha', 'Kaski', 'Lamjung', 'Manang', 'Mustang', 'Myagdi', 'Nawalpur', 'Parbat', 'Syangja', 'Tanahun'],
        'Lumbini': ['Arghakhanchi', 'Banke', 'Bardiya', 'Dang', 'Gulmi', 'Kapilvastu', 'Palpa', 'Pyuthan', 'Rolpa', 'Rupandehi', 'Rukum East', 'Nawalparasi West'],
        'Karnali': ['Dailekh', 'Dolpa', 'Humla', 'Jajarkot', 'Jumla', 'Kalikot', 'Mugu', 'Rukum West', 'Salyan', 'Surkhet'],
        'Sudurpashchim': ['Achham', 'Baitadi', 'Bajhang', 'Bajura', 'Dadeldhura', 'Darchula', 'Doti', 'Kailali', 'Kanchanpur'],
    }
    
    for branch in Branch.objects.all():
        if branch.state and branch.state in NEPAL_PROVINCE_DISTRICTS:
            # state is already a valid province
            branch.province = branch.state
            branch.district = NEPAL_PROVINCE_DISTRICTS[branch.state][0]
        else:
            # default to Bagmati (where Kathmandu is)
            branch.province = 'Bagmati'
            branch.district = 'Kathmandu'
        branch.save(update_fields=['province', 'district'])


class Migration(migrations.Migration):

    dependencies = [
        ('branch', '0003_alter_branch_options'),
    ]

    operations = [
        # First, add the new fields as nullable
        migrations.AddField(
            model_name='branch',
            name='district',
            field=models.CharField(
                blank=True,
                help_text='District in the selected province',
                max_length=100,
                null=True,
                validators=[apps.branch.models.validate_district]
            ),
        ),
        migrations.AddField(
            model_name='branch',
            name='province',
            field=models.CharField(
                blank=True,
                help_text='Province/Region in Nepal',
                max_length=100,
                null=True,
                validators=[apps.branch.models.validate_province]
            ),
        ),
        # Migrate data from state to province
        migrations.RunPython(migrate_state_to_province),
        # Now make province and district non-nullable
        migrations.AlterField(
            model_name='branch',
            name='province',
            field=models.CharField(
                help_text='Province/Region in Nepal',
                max_length=100,
                validators=[apps.branch.models.validate_province]
            ),
        ),
        migrations.AlterField(
            model_name='branch',
            name='district',
            field=models.CharField(
                help_text='District in the selected province',
                max_length=100,
                validators=[apps.branch.models.validate_district]
            ),
        ),
        # Finally, remove the old state field
        migrations.RemoveField(
            model_name='branch',
            name='state',
        ),
    ]
