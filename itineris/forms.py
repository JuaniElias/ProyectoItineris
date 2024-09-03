from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from .models import Company, Vehicle, Driver, Travel, Traveler, Period, Weekday, Segment, City, Waypoint, Nationality

from django import forms
from django_select2 import forms as s2forms


def validate_positive(value):
    if value <= 0:
        raise ValidationError('Debe ingresar un numero mayor que cero')


class CompanyCreationForm(UserCreationForm):
    class Meta:
        model = Company
        fields = ('username', 'email')


class CompanyChangeForm(UserChangeForm):
    class Meta:
        model = Company
        fields = ('username', 'email')



class CreateTravel(forms.Form):
    city_origin = forms.ModelChoiceField(queryset=City.objects.all(),
                                         label='Ciudad de salida',
                                         widget=s2forms.ModelSelect2Widget(
                                             model=City, search_fields=['city_name__icontains'],
                                         )
                                         )
    city_destination = forms.ModelChoiceField(queryset=City.objects.all(),
                                              label='Ciudad de destino',
                                              widget=s2forms.ModelSelect2Widget(model=City,
                                                                                search_fields=['city_name__icontains'],
                                                                                )
                                              )
    datetime_departure = forms.DateTimeField(label='Fecha y hora de salida',
                                             widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}),
                                             required=True)
    datetime_arrival = forms.DateTimeField(label='Fecha y hora estimada de llegada',
                                           widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}),
                                           required=True)
    addr_origin = forms.CharField(label='Dirección desde donde salís', required=True)
    addr_origin_num = forms.CharField(label='Número de la dirección', required=True)
    driver = forms.ModelChoiceField(label='Conductor', queryset=Driver.objects.none(), required=True)
    vehicle = forms.ModelChoiceField(label='Vehículo', queryset=Vehicle.objects.none(), required=True)

    def __init__(self, company_id, *args, **kwargs):
        super(CreateTravel, self).__init__(*args, **kwargs)
        self.fields['city_origin'].widget.attrs['class'] = 'form-control'
        self.fields['city_destination'].widget.attrs['class'] = 'form-control'
        self.fields['datetime_departure'].widget.attrs['class'] = 'form-control'
        self.fields['datetime_arrival'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin_num'].widget.attrs['class'] = 'form-control'
        self.fields['driver'] = forms.ModelChoiceField(queryset=Driver.objects.filter(company_id=company_id,
                                                                                      active=1))
        self.fields['driver'].widget.attrs['class'] = 'form-control'
        self.fields['vehicle'] = forms.ModelChoiceField(queryset=Vehicle.objects.filter(company_id=company_id,
                                                                                        status='Disponible',
                                                                                        active=1))
        self.fields['vehicle'].widget.attrs['class'] = 'form-control'


class CreateWaypoint(forms.ModelForm):
    city = forms.ModelChoiceField(queryset=City.objects.all(),
                                  label='Ciudad de destino',
                                  widget=s2forms.ModelSelect2Widget(model=City,
                                                                    search_fields=['city_name__icontains'],
                                                                    )
                                  )
    estimated_datetime_arrival = forms.DateTimeField(label='Fecha y hora de salida',
                                                     widget=forms.widgets.DateTimeInput(
                                                         attrs={'type': 'datetime-local'}),
                                                     )

    class Meta:
        model = Waypoint
        fields = ['city', 'estimated_datetime_arrival']

    def __init__(self, *args, **kwargs):
        super(CreateWaypoint, self).__init__(*args, **kwargs)
        self.fields['city'].widget.attrs['class'] = 'form-control'
        self.fields['estimated_datetime_arrival'].widget.attrs['class'] = 'form-control'


class EditSegment(forms.ModelForm):
    waypoint_origin = forms.ModelChoiceField(queryset=Waypoint.objects.all(), label='Ciudad de origen')
    waypoint_destination = forms.ModelChoiceField(queryset=Waypoint.objects.all(), label='Ciudad de destino')
    origin_display = forms.CharField()
    destination_display = forms.CharField()
    fee = forms.IntegerField(label='Tarifa', step_size=100)

    class Meta:
        model = Segment
        fields = ['waypoint_origin', 'waypoint_destination', 'origin_display', 'destination_display', 'fee']

    def __init__(self, *args, **kwargs):
        super(EditSegment, self).__init__(*args, **kwargs)
        self.fields['fee'].widget.attrs['class'] = 'form-control'
        self.fields['fee'].widget.attrs['style'] = 'width:120px'

        # Se esconden los campos verdaderos de la instancia
        self.fields['waypoint_origin'].widget = forms.HiddenInput()
        self.fields['waypoint_destination'].widget = forms.HiddenInput()

        # Mostrar los valores como texto no editable
        self.fields['origin_display'] = forms.CharField(
            initial=self.instance.waypoint_origin.city,
            label='Ciudad de origen',
            widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
        )
        self.fields['destination_display'] = forms.CharField(
            initial=self.instance.waypoint_destination.city,
            label='Ciudad de destino',
            widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
        )


EditSegmentFormSet = modelformset_factory(Segment, form=EditSegment, extra=0)

class PeriodTravel(forms.ModelForm):
    weekdays = forms.ModelMultipleChoiceField(queryset=Weekday.objects.all(),
                                              widget=s2forms.ModelSelect2MultipleWidget(
                                                  model=Weekday, search_fields=['weekday__icontains'],
                                                  attrs={'data-minimum-input-length': 0}),
                                              required=False)

    end_date = forms.DateField(label='Fin del periodo', widget=forms.widgets.DateInput(
        attrs={'type': 'date', 'id': 'period_end_date'}), required=False)

    class Meta:
        model = Period
        fields = ('weekdays', 'end_date',)

    def __init__(self, *args, **kwargs):
        super(PeriodTravel, self).__init__(*args, **kwargs)
        self.fields['weekdays'].widget.attrs['class'] = 'form-control'
        self.fields['end_date'].widget.attrs['class'] = 'form-control'


class CreateVehicle(forms.ModelForm):
    plate_number = forms.CharField(label='Patente', max_length=20, required=True)
    brand = forms.CharField(label='Marca', max_length=100)
    car_model = forms.CharField(label='Modelo', max_length=100)
    capacity = forms.IntegerField(label='Capacidad', validators=[validate_positive])
    color = forms.CharField(label='Color', required=False)

    class Meta:
        model = Vehicle
        fields = ('plate_number', 'brand', 'car_model', 'capacity', 'color',)

    def __init__(self, *args, **kwargs):
        super(CreateVehicle, self).__init__(*args, **kwargs)
        self.fields['plate_number'].widget.attrs['class'] = 'form-control'
        self.fields['brand'].widget.attrs['class'] = 'form-control'
        self.fields['car_model'].widget.attrs['class'] = 'form-control'
        self.fields['capacity'].widget.attrs['class'] = 'form-control'
        self.fields['color'].widget.attrs['class'] = 'form-control'


class CreateDriver(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', max_length=100, required=True)
    last_name = forms.CharField(label='Apellido', max_length=100, required=True)
    license_number = forms.CharField(label='Número de licencia', max_length=100, required=True)
    email = forms.EmailField(label='Email', max_length=100)
    phone_number = forms.CharField(label='Teléfono', max_length=100)

    class Meta:
        model = Driver
        fields = ('first_name', 'last_name', 'license_number', 'email', 'phone_number',)

    def __init__(self, *args, **kwargs):
        super(CreateDriver, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['license_number'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone_number'].widget.attrs['class'] = 'form-control'


class SearchTravel(forms.Form):
    NUMBER_CHOICES = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    ]

    city_origin = forms.ModelChoiceField(queryset=City.objects.all(),
                                         label='Ciudad de salida',
                                         widget=s2forms.ModelSelect2Widget(
                                             model=City, search_fields=['city_name__icontains'],
                                         )
                                         )
    city_destination = forms.ModelChoiceField(queryset=City.objects.all(),
                                              label='Ciudad de destino',
                                              widget=s2forms.ModelSelect2Widget(
                                                  model=City, search_fields=['city_name__icontains'],
                                              )
                                              )
    datetime_departure = forms.DateTimeField(label='Fecha Salida', required=True,
                                             widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    passengers = forms.ChoiceField(choices=NUMBER_CHOICES, label='Pasajeros', required=True)

    def __init__(self, *args, **kwargs):
        super(SearchTravel, self).__init__(*args, **kwargs)
        self.fields['city_origin'].widget.attrs['class'] = 'form-control'
        self.fields['city_destination'].widget.attrs['class'] = 'form-control'
        self.fields['datetime_departure'].widget.attrs['class'] = 'form-control'
        self.fields['passengers'].widget.attrs['class'] = 'form-control'


class CreateTraveler(forms.ModelForm):
    DOCUMENT_CHOICES = [
        ('DNI', 'DNI'),
        ('PASAPORTE', 'Pasaporte'),
        ('OTRO', 'Otro'),
    ]
    SEX_CHOICES = [
        ('M', 'M'),
        ('F', 'F'),
    ]
    first_name = forms.CharField(label='Nombre', max_length=50, required=True)
    last_name = forms.CharField(label='Apellido', max_length=50, required=True)
    dni_type = forms.ChoiceField(choices=DOCUMENT_CHOICES, label='Tipo de Documento', required=True)
    dni = forms.CharField(label='Número de documento', max_length=8, required=True)
    date_of_birth = forms.DateField(label='Fecha de nacimiento',
                                    widget=forms.widgets.DateInput(attrs={'type': 'date'})
                                    )
    sex = forms.ChoiceField(choices=SEX_CHOICES, label='Sexo', required=True)
    nationality = forms.ModelChoiceField(queryset=Nationality.objects.all().order_by('name'),
                                         label = 'Nacionalidad',
                                         widget=s2forms.ModelSelect2Widget(
                                             search_fields = ["name__icontains"],
                                             attrs = {
                                                "data-minimum-input-length": 0,
                                             })
                                         )
    email = forms.EmailField(label='Email', max_length=100, required=True)
    phone = forms.CharField(label='Teléfono', max_length=30, required=True)
    addr_ori = forms.CharField(label='Dirección origen', max_length=50, required=True)
    addr_ori_num = forms.CharField(label='Número dirección origen', max_length=50, required=True)
    addr_dest = forms.CharField(label='Dirección destino', max_length=50, required=True)
    addr_dest_num = forms.CharField(label='Número dirección destino', max_length=5, required=True)

    class Meta:
        model = Traveler
        fields = ('first_name', 'last_name',
                  'dni_type', 'dni', 'date_of_birth',
                  'sex', 'nationality', 'email', 'phone',
                  'addr_ori', 'addr_ori_num', 'addr_dest', 'addr_dest_num')

    def __init__(self, *args, **kwargs):
        super(CreateTraveler, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['dni_type'].widget.attrs['class'] = 'form-control'
        self.fields['dni'].widget.attrs['class'] = 'form-control'
        self.fields['date_of_birth'].widget.attrs['class'] = 'form-control'
        self.fields['sex'].widget.attrs['class'] = 'form-control'
        self.fields['nationality'].widget.attrs['class'] = 'form-control'
        self.fields['nationality'].widget.attrs['style'] = 'width: 220px;'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori_num'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest_num'].widget.attrs['class'] = 'form-control'


class UpdateTraveler(forms.ModelForm):
    phone = forms.CharField(label='Teléfono', max_length=30, required=True)
    addr_ori = forms.CharField(label='Dirección origen', max_length=50, required=True)
    addr_ori_num = forms.CharField(label='Número dirección origen', max_length=50, required=True)
    addr_dest = forms.CharField(label='Dirección destino', max_length=50, required=True)
    addr_dest_num = forms.CharField(label='Número dirección destino', max_length=5, required=True)

    class Meta:
        model = Traveler
        fields = ('phone', 'addr_ori', 'addr_ori_num', 'addr_dest', 'addr_dest_num')

    def __init__(self, *args, **kwargs):
        super(UpdateTraveler, self).__init__(*args, **kwargs)
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori'].widget.attrs['class'] = 'form-control'
        self.fields['addr_ori_num'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest'].widget.attrs['class'] = 'form-control'
        self.fields['addr_dest_num'].widget.attrs['class'] = 'form-control'


class UpdateTravel(forms.ModelForm):
    driver = forms.ModelChoiceField(label='Conductor', queryset=Driver.objects.none(), required=True)
    vehicle = forms.ModelChoiceField(label='Vehículo', queryset=Vehicle.objects.none(), required=True)
    addr_origin = forms.CharField(label='Dirección de salida', max_length=100, required=True)
    addr_origin_num = forms.CharField(label='Número', max_length=10, required=True)

    class Meta:
        model = Travel
        fields = ('driver', 'vehicle', 'addr_origin', 'addr_origin_num')

    def __init__(self, travel_id, *args, **kwargs):
        super(UpdateTravel, self).__init__(*args, **kwargs)

        # get Travel to get min_capacity to filter the vehicles
        travel = Travel.objects.get(travel_id=travel_id)
        company_id = travel.company_id
        min_capacity = travel.vehicle.capacity

        self.fields['driver'] = forms.ModelChoiceField(queryset=Driver.objects.filter(company_id=company_id,
                                                                                      active=1))
        self.fields['driver'].widget.attrs['class'] = 'form-control'
        self.fields['vehicle'] = forms.ModelChoiceField(queryset=Vehicle.objects.filter(company_id=company_id,
                                                                                        status='Disponible',
                                                                                        capacity__gte=min_capacity,
                                                                                        ))
        self.fields['vehicle'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin_num'].widget.attrs['class'] = 'form-control'
        self.fields['addr_origin'].widget.attrs['class'] = 'form-control'
