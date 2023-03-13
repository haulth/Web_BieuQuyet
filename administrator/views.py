
from django.shortcuts import render, reverse, redirect
from voting.models import Voter, Position, Candidate, Votes
from account.models import CustomUser
from account.forms import CustomUserForm
from voting.forms import *
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import re
from django_renderpdf.views import PDFView
from django.shortcuts import render
from datetime import datetime
from django.http import JsonResponse
import time


def save_vote_time(request):
    if request.method == 'POST':
        vote_time_str = request.POST.get('vote_time')
        vote_datetime = datetime.strptime(vote_time_str, '%Y-%m-%dT%H:%M')
        vote_time_str = vote_datetime.strftime('%Y-%m-%dT%H:%M')
        with open('vote_time.txt', 'w') as f:
            f.write(vote_time_str)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def delete_vote_time(request):
    if request.method == 'POST':
        # Xóa thông tin thời gian bầu cử trong file
        with open('vote_time.txt', 'w') as f:
            f.write('')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

    # return render(request, "admin/infomation_votes.html",time_left_str)

def find_n_winners(data, n):
    """Read More
    https://www.geeksforgeeks.org/python-program-to-find-n-largest-elements-from-a-list/
    """
    final_list = []
    candidate_data = data[:]
    # print("Candidate = ", str(candidate_data))
    for i in range(0, n):
        max1 = 0
        if len(candidate_data) == 0:
            continue
        this_winner = max(candidate_data, key=lambda x: x['votes'])
        # TODO: Check if None
        this = this_winner['name'] + \
            " với " + str(this_winner['votes']) + " lượt bình chọn"
        final_list.append(this)
        candidate_data.remove(this_winner)
    return ", &nbsp;".join(final_list)

class PrintView(PDFView):
    template_name = 'admin/print.html'
    prompt_download = True

    @property
    def download_name(self):
        named_tuple = time.localtime() # lấy struct_time
        time_string = time.strftime("%d/%m/%Y", named_tuple)
        return "Ketqua_{}.pdf".format(time_string)

    def get_context_data(self, *args, **kwargs):
        title = "E-voting"
        try:
            file = open(settings.ELECTION_TITLE_PATH, 'r', encoding='utf-8')
            title = file.read()
        except:
            pass
        context = super().get_context_data(*args, **kwargs)
        position_data = {}
        for position in Position.objects.all():
            candidate_data = []
            winner = ""
            for candidate in Candidate.objects.filter(position=position):
                this_candidate_data = {}
                votes = Votes.objects.filter(candidate=candidate).count()
                this_candidate_data['name'] = candidate.fullname
                this_candidate_data['votes'] = votes
                candidate_data.append(this_candidate_data)
            print("Candidate Data For  ", str(
                position.name), " = ", str(candidate_data))
            # ! Check Winner
            if len(candidate_data) < 1:
                winner = "Vị trí chưa có ứng viên"
            else:
                # Check if max_vote is more than 1
                if position.max_vote > 1:
                    winner = find_n_winners(candidate_data, position.max_vote)
                else:

                    winner = max(candidate_data, key=lambda x: x['votes'])
                    if winner['votes'] == 0:
                        winner = "Chưa có ai bỏ phiếu cho vị trí này."
                    else:
                        """
                        https://stackoverflow.com/questions/18940540/how-can-i-count-the-occurrences-of-an-item-in-a-list-of-dictionaries
                        """
                        count = sum(1 for d in candidate_data if d.get(
                            'votes') == winner['votes'])
                        if count > 1:
                            winner = f"Có {count} đại biểu với {winner['votes']} phiếu bầu"
                        else:
                            winner = "Người có số lượt cao nhất : " + winner['name']
            print("Candidate Data For  ", str(
                position.name), " = ", str(candidate_data))
            position_data[position.name] = {
                'candidate_data': candidate_data, 'winner': winner, 'max_vote': position.max_vote}
        context['positions'] = position_data
        print(context)
        return context

#thông tin về các vị trí và các ứng viên hiển thị lên bảng

def infoVoter(request):
    with open('vote_time.txt', 'r') as f:
        vote_time_str = f.read().strip()
    # Chuyển đổi thời gian kết thúc bình chọn từ định dạng string sang datetime object
    vote_time = datetime.fromisoformat(vote_time_str)

    # Tính thời gian còn lại đến khi kết thúc bình chọn
    time_left = vote_time - datetime.now()

    # Tính toán số giờ, phút và giây từ đối tượng timedelta
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Trả về thời gian còn lại dưới dạng chuỗi "giờ:phút:giây"
    time_left_str = f"{int(time_left.days * 24 + hours)}:{minutes:02d}:{seconds:02d}"
    print(time_left_str)

    positions = Position.objects.all().order_by('priority')
    candidates = Candidate.objects.all()
    voters = Voter.objects.all()
    voted_voters = Voter.objects.filter(voted=1)
    chart_data = {}

    for position in positions:
        if position.max_vote < 1:
            continue
            
        total_votes = Votes.objects.filter(candidate__position=position).count()
        candidates_data = []
        for candidate in Candidate.objects.filter(position=position):
            votes = Votes.objects.filter(candidate=candidate).count()
            percent = (votes / total_votes) * 100 if total_votes > 0 else 0
            candidates_data.append({'name': candidate.fullname, 'votes': votes, 'percent': percent})

        chart_data[position] = {'candidates': candidates_data, 'pos_id': position.id}

    context = {
        'time_left_str': time_left_str,
        'position_count': positions.count(),
        'candidate_count': candidates.count(),
        'voters_count': voters.count(),
        'voted_voters_count': voted_voters.count(),
        'chart_data': chart_data,
        'page_title': "Thống kê bầu cử"
    }
    return render(request, 'admin/infomation_votes.html', context)





def dashboard(request):
    positions = Position.objects.all().order_by('priority')
    candidates = Candidate.objects.all()
    voters = Voter.objects.all()
    voted_voters = Voter.objects.filter(voted=1)
    list_of_candidates = []
    votes_count = []
    chart_data = {}

    for position in positions:
        list_of_candidates = []
        votes_count = []
        for candidate in Candidate.objects.filter(position=position):
            list_of_candidates.append(candidate.fullname)
            votes = Votes.objects.filter(candidate=candidate).count()
            votes_count.append(votes)
        chart_data[position] = {
            'candidates': list_of_candidates,
            'votes': votes_count,
            'pos_id': position.id
        }

    context = {
        'position_count': positions.count(),
        'candidate_count': candidates.count(),
        'voters_count': voters.count(),
        'voted_voters_count': voted_voters.count(),
        'positions': positions,
        'chart_data': chart_data,
        'page_title': "Bảng điều khiển"
    }
    return render(request, "admin/home.html", context)


def voters(request):
    voters = Voter.objects.all()
    userForm = CustomUserForm(request.POST or None)
    voterForm = VoterForm(request.POST or None)
    context = {
        'form1': userForm,
        'form2': voterForm,
        'voters': voters,
        'page_title': 'Danh Sách Bỏ Phiếu'
    }
    if request.method == 'POST':
        if userForm.is_valid() and voterForm.is_valid():
            user = userForm.save(commit=False)
            voter = voterForm.save(commit=False)
            voter.admin = user
            user.save()
            voter.save()
            messages.success(request, "Người bỏ phiếu mới được tạo")
        else:
            messages.error(request, "Xác thực biểu mẫu không thành công")
    return render(request, "admin/voters.html", context)


def view_voter_by_id(request):
    voter_id = request.GET.get('id', None)
    voter = Voter.objects.filter(id=voter_id)
    context = {}
    if not voter.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        voter = voter[0]
        context['first_name'] = voter.admin.first_name
        context['last_name'] = voter.admin.last_name
        context['phone'] = voter.phone
        context['id'] = voter.id
        context['email'] = voter.admin.email
    return JsonResponse(context)


def view_position_by_id(request):
    pos_id = request.GET.get('id', None)
    pos = Position.objects.filter(id=pos_id)
    context = {}
    if not pos.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        pos = pos[0]
        context['name'] = pos.name
        context['max_vote'] = pos.max_vote
        context['id'] = pos.id
    return JsonResponse(context)


def updateVoter(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        instance = Voter.objects.get(id=request.POST.get('id'))
        user = CustomUserForm(request.POST or None, instance=instance.admin)
        voter = VoterForm(request.POST or None, instance=instance)
        user.save()
        voter.save()
        messages.success(request, "Cập nhật tiểu sử đại biểu")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('adminViewVoters'))


def deleteVoter(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        admin = Voter.objects.get(id=request.POST.get('id')).admin
        admin.delete()
        messages.success(request, "Đại biểu đã bị xóa")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('adminViewVoters'))


def viewPositions(request):
    positions = Position.objects.order_by('-priority').all()
    form = PositionForm(request.POST or None)
    context = {
        'positions': positions,
        'form1': form,
        'page_title': "Loại bình chọn"
    }
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.priority = positions.count() + 1  # Just in case it is empty.
            form.save()
            messages.success(request, "Đã Tạo Bình Chọn Mới")
        else:
            messages.error(request, "Lỗi biểu mẫu")
    return render(request, "admin/positions.html", context)


def updatePosition(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        instance = Position.objects.get(id=request.POST.get('id'))
        pos = PositionForm(request.POST or None, instance=instance)
        pos.save()
        messages.success(request, "Bình chọn đã được cập nhật")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('viewPositions'))


def deletePosition(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        pos = Position.objects.get(id=request.POST.get('id'))
        pos.delete()
        messages.success(request, "Bình chọn đã bị xóa")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('viewPositions'))


def viewCandidates(request):
    candidates = Candidate.objects.all()
    form = CandidateForm(request.POST or None, request.FILES or None)
    context = {
        'candidates': candidates,
        'form1': form,
        'page_title': 'Đại biểu'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            form = form.save()
            messages.success(request, "Ứng viên mới được tạo")
            
        else:
            messages.error(request, "Lỗi biểu mẫu")
    return render(request, "admin/candidates.html", context)


def updateCandidate(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        candidate_id = request.POST.get('id')
        candidate = Candidate.objects.get(id=candidate_id)
        form = CandidateForm(request.POST or None,
                             request.FILES or None, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật dữ liệu ứng viên")
        else:
            messages.error(request, "Biểu mẫu có lỗi")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('viewCandidates'))


def deleteCandidate(request):
    if request.method != 'POST':
        messages.error(request, "Truy cập bị từ chối")
    try:
        pos = Candidate.objects.get(id=request.POST.get('id'))
        pos.delete()
        messages.success(request, "Ứng viên đã bị xóa")
    except:
        messages.error(request, "Quyền truy cập vào tài nguyên này bị từ chối")

    return redirect(reverse('viewCandidates'))


def view_candidate_by_id(request):
    candidate_id = request.GET.get('id', None)
    candidate = Candidate.objects.filter(id=candidate_id)
    context = {}
    if not candidate.exists():
        context['code'] = 404
    else:
        candidate = candidate[0]
        context['code'] = 200
        context['fullname'] = candidate.fullname
        previous = CandidateForm(instance=candidate)
        context['form'] = str(previous.as_p())
    return JsonResponse(context)


def ballot_position(request):
    context = {
        'page_title': "Vị trí lá phiếu"
    }
    return render(request, "admin/ballot_position.html", context)


def update_ballot_position(request, position_id, up_or_down):
    try:
        context = {
            'error': False
        }
        position = Position.objects.get(id=position_id)
        if up_or_down == 'up':
            priority = position.priority - 1
            if priority == 0:
                context['error'] = True
                output = "Vị trí này đã ở trên cùng"
            else:
                Position.objects.filter(priority=priority).update(
                    priority=(priority+1))
                position.priority = priority
                position.save()
                output = "Ở trên"
        else:
            priority = position.priority + 1
            if priority > Position.objects.all().count():
                output = "Vị trí này đã ở dưới cùng"
                context['error'] = True
            else:
                Position.objects.filter(priority=priority).update(
                    priority=(priority-1))
                position.priority = priority
                position.save()
                output = "Ở dưới"
        context['message'] = output
    except Exception as e:
        context['message'] = e

    return JsonResponse(context)


def ballot_title(request):
    from urllib.parse import urlparse
    url = urlparse(request.META['HTTP_REFERER']).path
    from django.urls import resolve
    try:
        redirect_url = resolve(url)
        title = request.POST.get('title', 'Không Tên')
        file = open(settings.ELECTION_TITLE_PATH, 'w', encoding='utf-8')
        file.write(title)
        file.close()
        messages.success(
            request, "Tiêu đề bầu cử đã được thay đổi thành " + str(title))
        return redirect(url)
    except Exception as e:
        messages.error(request, e)
        return redirect("/")


def viewVotes(request):
    votes = Votes.objects.all()
    context = {
        'votes': votes,
        'page_title': 'Phiếu bầu'
    }
    return render(request, "admin/votes.html", context)


def resetVote(request):
    Votes.objects.all().delete()
    Voter.objects.all().update(voted=False, verified=False, otp=None)
    messages.success(request, "Tất cả phiếu bầu đã được đặt lại")
    return redirect(reverse('viewVotes'))
