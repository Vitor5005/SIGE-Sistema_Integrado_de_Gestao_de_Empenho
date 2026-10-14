from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastro', '0003_endereco_estado_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemgenerico',
            name='imagem',
            field=models.ImageField(blank=True, null=True, upload_to='generos/'),
        ),
    ]
